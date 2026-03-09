import httpx
import datetime
import dateutil.parser
import re
import logging
import asyncio
import json
from typing import Optional, Dict, List, Any

from app.services.whatsapp_ai_prompt import whatsapp_response
from app.services.ai_menu_generator import ai_menu_generator
from app.services.invoice_generator import generate_and_upload_invoice
from app.services.menu_services import get_service_provider_by_whatsapp, get_villa_code_by_name, get_service_base_price, get_villa_info_by_code
from app.services.order_summary import initiate_chat_session, active_chat_sessions, save_order_to_db, format_order_summary, check_order_confirmation,order_sessions, update_order_confirmation, get_sender_id_by_order, get_order_by_number
from app.settings.config import settings
from app.db.session import order_collection, villa_code_collection, checkin_collection, inquiry_collection
from app.models.order_summary import Order
from typing import Dict
from app.services.websocket_managerr import ConnectionManager
from app.services.website_sess import website_sessions
from app.utils.language_lesson_whatsapp_fucntions import language_starting_message, language_yes_message, language_lesson_response, language_no_message
from app.services.payment_service import create_xendit_payment_with_distribution, update_order_with_payment_info
from app.utils.media_upload import process_whatsapp_passport

logger = logging.getLogger(__name__)

manager = ConnectionManager()

villa_code_sessions = {}
issue_reporting_sessions = {}

local_order_store: Dict[str, str] = {}

decline_sessions : Dict[str, str] = {}


TIME_SLOTS = [
    '08:00 AM - 10:00 AM',
    '10:00 AM - 12:00 AM',
    '12:00 PM - 2:00 PM',
    '02:00 PM - 4:00 PM',
    '04:00 PM - 6:00 PM',
    '06:00 PM - 8:00 PM'
]

async def fetch_explore_data(api_url: str, query: str, user_id: str):
    payload = {"query": query}
    params = {"user_id": user_id}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            print(f"DEBUG: Response from API: {data}")
            return data.get("response")
    except Exception as e:
        return e

language_lesson_sessions = {}
persistent_mode_sessions = {}
PERSISTENT_API_MAPPING = {
    "what_to_do_today?": {
        "url": f"{settings.BASE_URL}/what-to-do/chat/",  # Dynamic Base URL
        "fetch_func": fetch_explore_data
    },
    "things_to_do_in_bali":{
        "url": f"{settings.BASE_URL}/things-to-do-in-bali/chat",
        "fetch_func":fetch_explore_data
    },
    "event_calendar":{
        "url": f"{settings.BASE_URL}/event-calender/chat",
        "fetch_func": fetch_explore_data
    },
    "local_cousine_guide":{
        "url": f"{settings.BASE_URL}/local-cuisine/chat",
        "fetch_func": fetch_explore_data
    },
    "plan_my_trip!":{
        "url": f"{settings.BASE_URL}/plan-my-trip/chat",
        "fetch_func": fetch_explore_data
    },
    "currency_converter":{
        "url": f"{settings.BASE_URL}/currency-converter/chat",
        "fetch_func": fetch_explore_data
    },
}

from app.services.menu_services import get_main_menu_design

async def fetch_menu_data(api_url: str, menu_type: str) -> list:
    try:
        data = await get_main_menu_design()
        if data is None or data.empty or "Menu Location" not in data.columns:
            return []
        filtered_data = data[data["Menu Location"] == menu_type]
        if filtered_data.empty:
            return []
        result = []
        for _, row in filtered_data.iterrows():
            result.append({
                "id":row["Title"].lower().replace(" ", "_"),
                "title": row["Title"],
                "picture": row["Picture"],
                "description": row["Description"],
                "button": row["Button"]
            })
        return result
    except Exception as e:
        print(f" Error fetching menu data locally: {e}")
        return []
    
### Fetch Submenu Data
async def fetch_submenu_data(api_url: str):
    from app.services.menu_services import get_sub_menu
    try:
        # api_url looks like /menu/sub/{main_menu}
        main_menu = api_url.split("/")[-1]
        return await get_sub_menu(main_menu)
    except Exception as e:
        print(f" Error fetching submenu data locally: {e}")
        return []

async def fetch_service_items(api_url: str, subcategory: str) -> list:
    from app.services.menu_services import get_service_items
    try:
        return await get_service_items(subcategory)
    except Exception as e:
        print(f"Error fetching service items locally: {e}")
        return []
    
async def fetch_menu_design(main_menu: str) -> dict: 
    from app.services.menu_services import get_order_service_sub_menu, get_restaurants_menu, get_sub_menu
    try:
        if main_menu == "Order Services":
            return await get_order_service_sub_menu(main_menu)
        elif main_menu in ["Restaurants", "For the 'gram"]:
            return await get_restaurants_menu(main_menu)
        else:
            return await get_sub_menu(main_menu)
    except Exception as e:
        print(f"Error fetching service items locally: {e}")
        return {}
    

async def fetch_whatsapp_numbers(serviceitem: str):
    from app.services.menu_services import get_service_overview, get_service_providers
    try:
        design_df = await get_service_overview()
        providers_df = await get_service_providers()
        
        # Robust name matching - normalize both sides
        service_norm = re.sub(r'[^a-zA-Z0-9]', '', serviceitem.lower())
        design_df['norm_item'] = design_df["Service Item"].apply(lambda x: re.sub(r'[^a-zA-Z0-9]', '', str(x).lower()))
        
        matching_items = design_df[design_df["norm_item"] == service_norm]
        if matching_items.empty:
            # Fallback for partial matches
            matching_items = design_df[design_df["norm_item"].str.contains(service_norm, na=False)]
            
        if matching_items.empty:
            logger.warning(f"⚠️ No service items found for '{serviceitem}' to notify providers.")
            return []

        # Parse provider IDs with more robustness
        all_ids = []
        for ids_str in matching_items["Service Providers"].fillna("").astype(str):
            # Split by comma or semicolon and strip spaces
            ids = [i.strip() for i in re.split(r'[,;]', ids_str) if i.strip()]
            all_ids.extend(ids)
            
        unique_provider_ids = list(set(all_ids))
        logger.info(f"🔍 Found provider IDs {unique_provider_ids} for service '{serviceitem}'")
        
        # Match providers by ID (Number column)
        matching_providers = providers_df[providers_df["Number"].astype(str).str.strip().isin(unique_provider_ids)]
        
        if matching_providers.empty:
            logger.warning(f"⚠️ No providers in sheet match IDs {unique_provider_ids}")
            return []
            
        # Clean the WhatsApp numbers - MUST be digits only FOR WHATSAPP API
        final_numbers = []
        for num in matching_providers["WhatsApp"].tolist():
            clean_num = re.sub(r'[^\d]', '', str(num))
            
            # Indonesian Number Normalization: Convert 08xxx to 628xxx
            if clean_num.startswith('0'):
                clean_num = '62' + clean_num[1:]
            # If it starts with 8, it's likely missing the prefix entirely
            elif clean_num.startswith('8'):
                clean_num = '62' + clean_num
                
            if clean_num:
                final_numbers.append(clean_num)
                
        logger.info(f"✅ Normalized WhatsApp numbers: {final_numbers}")
        return final_numbers
    except Exception as e:
        logger.error(f"Error fetching whatsapp numbers for provider notification: {e}")
        return []
    


async def send_typing_indicator(phone_number: str, message_id: str):
    """Send typing indicator to show bot is processing"""
    
    headers = {
        "Authorization": f"Bearer {settings.access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ Typing indicator sent to {phone_number}")
    except Exception as e:
        print(f"❌ Failed to send typing indicator: {e}")





async def send_whatsapp_order_to_SP(recipient_number: str, order_summary: dict):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        order_summary_text = format_order_summary(order_summary)
        orderid = order_summary['order_number']

        header = (
            "New request received! Please confirm or decline availability.\n"
            "_Permintaan layanan baru diterima! Harap konfirmasi atau tolak ketersediaan._"
        )
        footer = (
            "Please respond within 60 sec to secure this request.\n"
            "_Harap tanggapi dalam 60 sec untuk mengamankan permintaan ini._"
        )

        full_message = f"{header}\n\n{order_summary_text}\n\n{footer}"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {"type": "text", "text": "📌 New Service Request"},
                "body": {"text": full_message},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": orderid,
                                "title": "✅ Accept"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"decline_{orderid}",
                                "title": "❌ Decline"
                            }
                        }
                    ]
                }
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return None

    return response.json()



async def send_interactive_message(recipient_id, payment_result):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }

        payment_message = f"""Thank you for choosing EASY Bali. Please confirm your order by completing the payment through the secure link below. Once payment is confirmed, we’ll take care of the rest — just sit back, relax, and your service will come to you as scheduled."""

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "header": {
                    "type": "text",
                    "text": "🌴 Your Order Awaits!"
                },
                "body": {
                    "text": payment_message
                },
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": "Pay Now",
                        "url": payment_result['payment_url']
                    }
                }
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return None

    return response.json()




async def send_confirmation_order_to_SP(recipient_number: str, order_number: str):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": f"Are you sure you want to accept this request? The guest will be notified immediately.\n" "_Apakah Anda yakin ingin menerima permintaan ini? Tamu akan segera diberitahu._"},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"yes_order_{order_number}",
                                "title": "Yes"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"no_order_{order_number}",
                                "title": "No"
                            }
                        }
                    ]
                }
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return None

    return response.json()



async def send_whatsapp_interactive_link(recipient_number: str, link: str):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {
                "text": f"Please click the button below to open the link."
            },
            "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": "Open link",
                "url": link
            }
    }
        }
    }
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return None

    return response.json()





async def send_whatsapp_card(recipient_id: str, card_data: dict):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        title = card_data.get("title") or card_data.get("category") or card_data.get("service_item")
        button_title = card_data.get("button", "See options")
        description = card_data.get("description") or card_data.get("Description")
        # picture = card_data.get("picture", "")

        button_id = title.replace(" ", "_")

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {"type": "text", "text": title},
                "body": {"text": description},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": button_id, "title": button_title}}
                    ]
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ WhatsApp API Response: {response.status_code}, {response.text}")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error sending WhatsApp card: {e.response.status_code}, {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected Error sending WhatsApp card: {e}")
        


async def send_whatsapp_card_with_link(recipient_id: str, card_data: dict):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        title = card_data.get("title") or card_data.get("category") or card_data.get("service_item")
        button_title = card_data.get("button", "See options")
        link = card_data.get("link", "No links available")
        description = card_data.get("Description", "No description available")

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "header": {"type": "text", "text": title},
                "body": {"text": description},
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": button_title,
                        "url": link
                    },
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ WhatsApp API Response: {response.status_code}, {response.text}")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error sending WhatsApp card: {e.response.status_code}, {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected Error sending WhatsApp card: {e}")




async def send_whatsapp_list_message(recipient_id: str, card_data: dict):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        title = card_data.get("title", "Untitled")
        description = card_data.get("description", "No description available")

        if len(description) > 72:
            description = description[:69] + "..."

        sections = [
            {
                "title": "Available Options",
                "rows": [
                    {
                        "id": option["id"],
                        "title": option["service_title"],
                        "description": option["service_description"][:69] + "..."
                        if len(option["service_description"]) > 72
                        else option["service_description"]
                    }
                    for option in card_data.get("sections", [])
                ],
            }
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": title},
                "body": {"text": description},
                "footer": {"text": "Tap on an View Options"},
                "action": {
                    "button": "View Options",
                    "sections": sections,
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ WhatsApp API Response: {response.status_code}, {response.text}")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error sending WhatsApp list: {e.response.status_code}, {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected Error sending WhatsApp list: {e}")

async def send_whatsapp_menu_list_message(recipient_id: str, card_data: dict):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        title = card_data.get("main_title", "Untitled")
        description = card_data.get("main_description", "No description available")

        if len(description) > 72:
            description = description[:69] + "..."
        sections = [
            {
                "title": "Available Options",
                "rows": [
                    {
                        "id": f"{item['category'].lower().replace(' ', '_')}",  # Create ID from category
                        "title": item["category"][:24],  # WhatsApp limit is 24 chars for title
                        "description": item["description"][:69] + "..."
                        if len(item["description"]) > 72
                        else item["description"]
                    }
                    for item in card_data.get("items", [])
                ],
            }
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": f"*{title}*\n{description}"},
                "footer": {"text": "Tap to view options"},
                "action": {
                    "button": "View Options",
                    "sections": sections,
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ WhatsApp Category List Sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Error sending Category list: {e}")

async def send_whatsapp_subcategory_list_message(recipient_id: str, card_data: dict, category_name: str):
    """Send secondary list for subcategories"""
    try:
        headers = {"Authorization": f"Bearer {settings.access_token}", "Content-Type": "application/json"}
        sections = [{
            "title": f"{category_name} - Subcategories",
            "rows": [{
                "id": f"subcat_{item['subcategory'].lower().replace(' ', '_')}",
                "title": item["subcategory"][:24],
                "description": item["description"][:69] + "..." if len(item["description"]) > 72 else item["description"]
            } for item in card_data]
        }]
        payload = {
            "messaging_product": "whatsapp", "to": recipient_id, "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": f"📍 *{category_name}*\nSelect a sub-category below to explore our services."},
                "footer": {"text": "Tap to view subcategories"},
                "action": {"button": "Select Option", "sections": sections}
            }
        }
        async with httpx.AsyncClient() as client:
            await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
    except Exception as e:
        print(f"❌ Error sending Subcategory list: {e}")

async def send_whatsapp_service_list_message(recipient_id: str, card_data: dict, subcategory_name: str):
    """Send tertiary list for service items (the 'Book' list)"""
    try:
        headers = {"Authorization": f"Bearer {settings.access_token}", "Content-Type": "application/json"}
        sections = [{
            "title": f"Services for {subcategory_name}",
            "rows": [{
                "id": f"service_{item['title'].lower().replace(' ', '_')}",
                "title": item["title"][:24],
                "description": f"💰 IDR {item['button']} | Tap to Book Now"
            } for item in card_data]
        }]
        payload = {
            "messaging_product": "whatsapp", "to": recipient_id, "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": f"🛎️ *{subcategory_name} - Available Services*\nChoose a service below to start your booking."},
                "footer": {"text": "Easy Bali - Instant Booking ✨"},
                "action": {"button": "Book Now", "sections": sections}
            }
        }
        async with httpx.AsyncClient() as client:
            await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
    except Exception as e:
        print(f"❌ Error sending Service list: {e}")

async def send_ai_whatsapp_list_message(
    recipient_id: str,
    menu_data: Dict[str, Any],
    button_text: str = "View Options",
    footer_text: str = "Powered by EASYBali ✨"
) -> bool:
    try:
        image_url = menu_data.get("image_url")
        title = str (menu_data.get("title", "Our Services"))
        body_text = (
            f"✨ *{title}*\n\n"
            f"We found some great services for you! Tap the button below to view the full details and explore available options."
        )
    
        raw_sections: List[Dict] = menu_data.get("sections", [])
        all_rows = []
        for section in raw_sections:
            all_rows.extend(section.get("rows", []))

        if not all_rows:
            print("⚠️ No rows found in menu_data – skipping list message")
            return False

        whatsapp_rows = []
        for idx, item in enumerate(all_rows):
            row_id = item.get("id")
            if not row_id:
                row_id = f"row_{idx}_{recipient_id[-4:]}"  # fallback unique ID

            title = (
                item.get("service_title")
                or item.get("title")
                or "Untitled Option"
            )[:60]  # Max title length

            description = (
                item.get("service_description")
                or item.get("description")
                or ""
            )
            if len(description) > 72:
                description = description[:69] + "..."

            whatsapp_rows.append({
                "id": str(row_id),
                "title": title,
                "description": description
            })

        if len(whatsapp_rows) > 10:
            whatsapp_rows = whatsapp_rows[:10]

        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        # If an image is available, send it first as a caption
        if image_url:
            await send_whatsapp_image_with_caption(
                recipient_id,
                image_url,
                body_text[:1024]
            )

        # Now send the proper list message (cta_url does NOT support sections)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": "✨ Tap *View Options* below to browse and select your service:"
                },
                "footer": {
                    "text": footer_text[:60]
                },
                "action": {
                    "button": button_text[:20],
                    "sections": [
                        {
                            "title": "Available Services",
                            "rows": whatsapp_rows
                        }
                    ]
                }
            }
        }

        async with httpx.AsyncClient(timeout=50.0) as client:
            response = await client.post(
                f"{settings.whatsapp_api_url}",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

        print(f"✅ WhatsApp List Message sent successfully to {recipient_id}")
        return True

    except httpx.HTTPStatusError as exc:
        print(f"❌ WhatsApp API error {exc.response.status_code}: {exc.response.text}")
        return False
    except Exception as exc:
        print(f"❌ Failed to send WhatsApp list message: {exc}")
        import traceback
        traceback.print_exc()
        return False
    


async def send_whatsapp_menu_list_message(recipient_id: str, card_data: dict):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        title = "EASYBali Menu"
        description = "Choose from our available services"

        if len(description) > 72:
            description = description[:69] + "..."

        # Create rows for all menu items
        rows = []
        for item in card_data["data"]:
            rows.append({
                "id": item["id"],
                "title": item["title"],
                "description": item["description"][:69] + "..."
                if len(item["description"]) > 72
                else item["description"]
            })

        sections = [
            {
                "title": "Available Options",
                "rows": rows,
            }
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": title},
                "body": {"text": description},
                "footer": {"text": "Tap on an option to continue"},
                "action": {
                    "button": "View Options",
                    "sections": sections,
                },
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ WhatsApp API Response: {response.status_code}, {response.text}")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error sending WhatsApp list: {e.response.status_code}, {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected Error sending WhatsApp list: {e}")


async def send_calendar_flow(recipient_id: str):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        # Flow JSON configuration
        flow_json = {
            "version": "6.3",
            "data_api_version": "3.0",
            "screens": [
                {
                    "id": "DATE_PICKER_SCREEN",
                    "terminal": True,
                    "layout": {
                        "type": "SingleColumnLayout",
                        "children": [
                            {
                                "type": "CalendarPicker",
                                "name": "selected_date",
                                "label": "Select Appointment Date",
                                "helper-text": "Choose today or a future date",
                                "required": True,
                                "mode": "single",
                                "min-date": "${date.today}",
                                "include-days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                            },
                            {
                                "type": "Footer",
                                "label": "Confirm Date",
                                "on-click-action": {
                                    "name": "complete_flow"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        # Construct payload
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "body": {"text": "Please select a date"},
                "flow_json": flow_json
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.whatsapp_api_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            print(f"✅ Calendar flow sent to {recipient_id}: {response.status_code}")

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error sending calendar flow: {e.response.status_code}")
        print(f"Response content: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error sending calendar flow: {str(e)}")
        raise  # Re-raise for potential upstream handling


async def starting_message(recipient_number: str):
    try:
        from app.services.menu_services import get_villa_info_by_code
        villa_code = await get_user_villa_code(recipient_number)
        villa_info = await get_villa_info_by_code(villa_code) if villa_code else None
        
        welcome_header = "🌴 Welcome to EASYBali! 🌴"
        if villa_info:
            welcome_header = f"🌴 Welcome to {villa_info.get('name', 'EASYBali')}! 🌴"

        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": welcome_header
                },
                "body": {
                    "text": (
                        "I’m here to assist you with anything you need during your Bali experience. Whether it's ordering services like transportation, massage, or food, or finding the best spots to visit, I’ve got you covered!\n\n"
                        "What can I help you with today? Feel free to ask anything, and I’ll be happy to assist you! 😊"
                    )
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "menu_button",
                                "title": "Menu"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "chat_button",
                                "title": "Chat with Us"
                            }
                        }
                    ]
                }
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return None

    return response.json()



async def perform_arrival_confirmation(sender_id: str, villa_code: str):
    """Logs check-in, notifies manager, and activates guest profile."""
    try:
        villa_info = await get_villa_info_by_code(villa_code)
        villa_name = villa_info.get("name") if villa_info else f"Villa {villa_code}"
        
        # 1. Log to DB
        checkin_data = {
            "sender_id": sender_id,
            "villa_code": villa_code,
            "villa_name": villa_name,
            "checkin_time": datetime.datetime.now(),
            "status": "active"
        }
        await checkin_collection.update_one(
            {"sender_id": sender_id, "status": "active"},
            {"$set": checkin_data},
            upsert=True
        )
        
        # 2. Notify Manager
        if villa_info and villa_info.get("manager_number"):
            manager_num = str(villa_info["manager_number"]).strip()
            # Ensure manager_num is clean (no +, just digits)
            clean_mgr = "".join(filter(str.isdigit, manager_num))
            
            manager_msg = (
                f"🔔 *New Guest Arrival!*\n\n"
                f"Guest `{sender_id}` has just checked into *{villa_name}* ({villa_code}).\n\n"
                f"Access is now granted for concierge services."
            )
            await send_whatsapp_message(clean_mgr, manager_msg)
            logger.info(f"Check-in notification sent to Manager {clean_mgr} for {villa_name}")

        # 3. Activation confirmation to guest
        wifi_info = ""
        if villa_info and villa_info.get("wifi_name"):
            wifi_info = f"\n\n📶 *WiFi Details:*\nName: `{villa_info['wifi_name']}`\nPass: `{villa_info.get('wifi_password', 'N/A')}`"
            
        map_link = f"\n📍 *Villa Location:* {villa_info['map_link']}" if villa_info and villa_info.get("map_link") else ""

        guest_conf = (
            f"✅ *Arrival Confirmed!*\n\n"
            f"Hi {sender_id[-4:]}, welcome to *{villa_name}*. Your profile is now active.{wifi_info}{map_link}\n\n"
            f"I am your virtual concierge. Type *Order Services* to see what I can do for you, or ask me anything about the villa!"
        )
        await send_whatsapp_message(sender_id, guest_conf)
        
        return True
    except Exception as e:
        logger.error(f"Error in perform_arrival_confirmation for {sender_id}: {e}")
        return False


async def log_guest_inquiry(sender_id: str, villa_code: str, query: str, response: str, intent: str = "general"):
    """Logs a guest's question/interaction to the database for oversight."""
    try:
        inquiry_doc = {
            "sender_id": sender_id,
            "villa_code": villa_code,
            "query": query,
            "response": response,
            "intent": intent,
            "timestamp": datetime.datetime.now(),
            "status": "responded"
        }
        await inquiry_collection.insert_one(inquiry_doc)
        logger.info(f"Logged inquiry from {sender_id} at {villa_code}")
        
        # If it's a support request, notify manager immediately
        if intent == "support_request":
            villa_info = await get_villa_info_by_code(villa_code)
            if villa_info and villa_info.get("manager_number"):
                mgr_num = "".join(filter(str.isdigit, str(villa_info["manager_number"])))
                mgr_msg = (
                    f"🆘 *Support Requested!*\n\n"
                    f"Villa: *{villa_info.get('name')}*\n"
                    f"Guest ID: `{sender_id[-4:]}`\n"
                    f"The guest has requested to speak with us. Please respond as soon as possible."
                )
                await send_whatsapp_message(mgr_num, mgr_msg)
    except Exception as e:
        logger.error(f"Failed to log inquiry: {e}")

async def send_decline_confirmation(recipient_number: str, order_num: str):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "Are you sure you want to decline this request? This action cannot be undone.\nApakah Anda yakin ingin menolak permintaan ini? Tindakan ini tidak dapat dibatalkan."
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"confirm_decline_{order_num}",
                                "title": "Yes, Decline"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"cancel_decline_{order_num}",
                                "title": "No, Go Back"
                            }
                        }
                    ]
                }
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error sending decline confirmation: {e}")
        return None

async def get_user_villa_code(sender_id: str):
    try:
        user_data = await villa_code_collection.find_one({"sender_id": sender_id})
        return user_data.get("villa_code") if user_data else None
    except Exception as e:
        print(f"Error getting villa code for {sender_id}: {e}")
        return None

async def save_user_villa_code(sender_id: str, villa_code: str):
    try:
        await villa_code_collection.update_one(
            {"sender_id": sender_id},
            {
                "$set": {
                    "sender_id": sender_id,
                    "villa_code": villa_code,
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving villa code for {sender_id}: {e}")
        return False

def is_valid_villa_code(villa_code: str):
    pattern = r'^V\d+$'
    return bool(re.match(pattern, villa_code.upper()))

async def send_villa_code_request(sender_id: str):
    """Send villa code request message"""
    message = (
        "🏝️ Welcome to EASY Bali! 🏝️\n\n"
        "To provide you with the best service, please share your Villa Code.\n\n"
        "Your Villa Code should be in the format: V1, V2, V3, etc.\n\n"
        "Please enter your Villa Code:"
    )
    await send_whatsapp_message(sender_id, message)


async def send_invoice_with_download(sender_id: str, download_url: str, order_number: str):
    try:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": sender_id,
            "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "header": {
                    "type": "text",
                    "text": "📄 Your Invoice is Ready!"
                },
                "body": {
                    "text": f"Thank you for your payment! Your invoice for order {order_number} is now available for download.\n\n✅ Payment confirmed\n📄 Invoice generated\n⬇️ Click below to download"
                },
                "footer": {
                    "text": "Invoice expires in 24 hours"
                },
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": "Download Invoice",
                        "url": download_url
                    }
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Invoice download message sent successfully to {sender_id} for order {order_number}")
                return True
            else:
                logger.error(f"Failed to send invoice message. Status: {response.status_code}, Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error(f"Timeout sending invoice message to {sender_id}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error sending invoice message to {sender_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending invoice message to {sender_id}: {e}")
        return False
    

async def send_whatsapp_flow_message(recipient_id: str, order_number: str):
    """Send WhatsApp Flow message to user"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        FLOW_ID = "24190558223942158"  # Your Flow ID
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {
                    "type": "text",
                    "text": "📅 Appointment Booking"
                },
                "body": {
                    "text": f"Please select your preferred appointment date for order #{order_number}.\n\nTap the button below to open the date picker."
                },
                "footer": {
                    "text": "Easy Bali Services"
                },
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": order_number,
                        "flow_id": FLOW_ID,
                        "flow_cta": "Select Date",
                        "flow_action": "navigate"
                    }
                }
            }
        }
    
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ WhatsApp API error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return None
                
            response.raise_for_status()
            result = response.json()
            print(f"✅ Flow message sent successfully to {recipient_id}")
            print(f"📱 Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            return result
            
    except httpx.TimeoutException:
        print(f"❌ Timeout error sending flow message to {recipient_id}")
        return None
    except Exception as e:
        print(f"❌ Error sending flow message: {e}")
        import traceback
        traceback.print_exc()
        return None
    

async def send_whatsapp_service_flow_message(recipient_id: str, flow_token: str):
    """Send WhatsApp Service Selection Flow message to user"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        # ⚠️ VERIFY THIS IS THE CORRECT FLOW ID
        SERVICE_FLOW_ID = "2282521258887998" 
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {
                    "type": "text",
                    "text": "🛍️ Service Selection"
                },
                "body": {
                    "text": "Please select your preferred service from our available options.\n\nTap the button below to browse and select your service."
                },
                "footer": {
                    "text": "Easy Bali Services"
                },
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": flow_token,
                        "flow_id": SERVICE_FLOW_ID,
                        "flow_cta": "Select Service",
                        "flow_action": "data_exchange"
                    }
                }
            }
        }
        
        print(f"🔍 DEBUG: Full payload: {json.dumps(payload, indent=2)}")
    
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            
            print(f"🔍 DEBUG: WhatsApp API response status: {response.status_code}")
            print(f"🔍 DEBUG: WhatsApp API response: {response.text}")
            
            if response.status_code != 200:
                print(f"❌ WhatsApp API error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return None
                
            response.raise_for_status()
            result = response.json()
            print(f"✅ Service flow message sent successfully to {recipient_id}")
            print(f"📱 Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            return result
            
    except Exception as e:
        print(f"❌ Error sending service flow message: {e}")
        import traceback
        traceback.print_exc()
        return None
    

async def send_whatsapp_order_flow_message(recipient_id: str, flow_token: str):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        # ⚠️ VERIFY THIS IS THE CORRECT FLOW ID
        SERVICE_FLOW_ID = "1343770641089909" 
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {
                    "type": "text",
                    "text": "🛍️ EASYBali Services"
                },
                "body": {
                    "text": "Please select your preferred service from our available options.\n\nTap the button below to browse and select your service."
                },
                "footer": {
                    "text": "Easy Bali Catelog"
                },
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": flow_token,
                        "flow_id": SERVICE_FLOW_ID,
                        "flow_cta": "Select Service",
                        "flow_action": "data_exchange"
                    }
                }
            }
        }
    
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            
            print(f"🔍 DEBUG: WhatsApp API response status: {response.status_code}")
            print(f"🔍 DEBUG: WhatsApp API response: {response.text}")
            
            if response.status_code != 200:
                print(f"❌ WhatsApp API error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return None
                
            response.raise_for_status()
            result = response.json()
            print(f"✅ Service flow message sent successfully to {recipient_id}")
            print(f"📱 Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            return result
            
    except Exception as e:
        print(f"❌ Error sending service flow message: {e}")
        import traceback
        traceback.print_exc()
        return None
    



async def send_ai_whatsapp_order_flow_message(recipient_id: str, flow_token: str, menu_data: Dict[str, Any]):
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json"
        }
        
        SERVICE_FLOW_ID = "707681682414552"

        image_url = menu_data.get("image_url")
        title = str(menu_data.get("title", "Our Services"))
        body_text = (
            f"Ready to enjoy our premium *{title}* experience. Select your preferred item below."
        )

        # Extract service items from rows
        rows = menu_data.get("sections", [{}])[0].get("rows", [])
        service_items = []
        for row in rows:
            service_items.append({
                "id": row.get("id"),
                "title": row.get("title"),
                "description": row.get("description"),
                "metadata": row.get("price")
            })
        
        # Get today's date for calendar
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {
                    "type": "image",
                    "image": {
                        "link": image_url
                    }
                },
                "body": {
                    "text": body_text
                },
                "footer": {
                    "text": "Powered by EASYBali ✨"
                },
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": flow_token,
                        "flow_id": SERVICE_FLOW_ID,
                        "flow_cta": "Select Service",
                        "flow_action": "navigate", 
                        "flow_action_payload": {  
                            "screen": "SERVICE_AND_DATE_SELECTION",
                            "data": {
                                "service_items": service_items,
                                "min_date": today,
                                "today_date": today,
                                "flow_token": flow_token
                            }
                        }
                    }
                }
            }
        }
    
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            
            print(f"🔍 DEBUG: WhatsApp API response status: {response.status_code}")
            print(f"🔍 DEBUG: WhatsApp API response: {response.text}")
            
            if response.status_code != 200:
                print(f"❌ WhatsApp API error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return None
                
            response.raise_for_status()
            result = response.json()
            print(f"✅ Service flow message sent successfully to {recipient_id}")
            print(f"📱 Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            return result
            
    except Exception as e:
        print(f"❌ Error sending service flow message: {e}")
        import traceback
        traceback.print_exc()
        return None




def extract_villa_name(text: str):
    # Robust extraction: Capture everything after "Hi, I am in"
    match = re.search(r"Hi,\s*I\s*am\s*in\s+(.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback to the old "word after villa" logic if regex fails
    words = text.split()
    for i, word in enumerate(words):
        if word.lower() == "villa" and i + 1 < len(words):
            return f"Villa {words[i + 1]}"
    return None


async def get_ai_chatbot_response(query: str, user_id: str) -> Optional[str]:
    """
    Calls the AI chatbot endpoint to generate a response
    """
    try:
        async with httpx.AsyncClient(timeout=50.0) as client:
            response = await client.post(
                f"{settings.BASE_URL}/chatbot/generate-response",
                json={"query": query},
                params={"user_id": user_id}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response") or data.get("message")
    except Exception as e:
        print(f"Error calling AI chatbot: {e}")
        return None
    
async def send_whatsapp_image_with_caption(recipient_id: str, image_url: str, caption: str):
    """Send image with caption via WhatsApp"""
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.whatsapp_api_url, 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            print(f"✅ Image sent to {recipient_id}")
            
    except Exception as e:
        print(f"❌ Error sending image: {e}")


async def process_message(sender_id: str, message_payload: dict, message_id:str):
    start_time = datetime.datetime.now()
    try:
        logger.info(f"📩 Processing message {message_id} from {sender_id}")
        await send_typing_indicator(sender_id, message_id)

        message_text = None
        serviceitems_text = None
        category_text = None
        selected_id = None

        if "text" in message_payload:
            message_text = message_payload["text"]["body"].strip()
        elif "audio" in message_payload:
            message_text = "VOICE_NOTE" # Signal it's a voice note for processing
            audio_id = message_payload["audio"]["id"]
        elif "image" in message_payload or "document" in message_payload or "audio" in message_payload:
            # Handle media uploads for passport/document submission OR issues
            media_info = message_payload.get("image") or message_payload.get("document") or message_payload.get("audio")
            media_id = media_info.get("id")
            
            if media_id:
                # If guest is in issue reporting mode, we let the lower logic handle it
                if sender_id in issue_reporting_sessions:
                    pass # Continue to specific handler
                else:
                    # Default: Assume Passport for image/document
                    if "image" in message_payload or "document" in message_payload:
                        user_villa_code = await get_user_villa_code(sender_id) or "UNKNOWN"
                        success, msg = await process_whatsapp_passport(sender_id, media_id, user_villa_code)
                        await send_whatsapp_message(sender_id, msg)
                        return
                    else:
                        # Audio outside of session? Maybe just ignore or pass to AI
                        pass
        elif "interactive" in message_payload:
            persistent_mode_sessions.pop(sender_id, None)
            language_lesson_sessions.pop(sender_id, None)
            interactive_type = message_payload["interactive"].get("type")

            if interactive_type == "button_reply":
                category_text = message_payload["interactive"]["button_reply"]["title"]
                button_id = message_payload["interactive"]["button_reply"]["id"]

                # --- Existing button_reply logic ---
                if button_id.startswith("confirm_decline_"):
                    order_num = button_id.split("_", 2)[2]
                    await send_whatsapp_message(
                        sender_id,
                        "Thank you for confirming. We've noted your unavailability for this request.\n"
                        "_Terima kasih telah mengonfirmasi. Kami telah mencatat ketidaksediaan Anda untuk permintaan ini._"
                    )
                    await order_collection.update_one(
                        {"order_number": order_num},
                        {"$set": {"status": "declined"}}
                    )
                    decline_sessions.pop(sender_id, None)
                    return

                if button_id.startswith("cancel_decline_"):
                    order_num = button_id.split("_", 2)[2]
                    order = await get_order_by_number(order_num)
                    if order and order.get("status") == "pending":
                        await send_whatsapp_order_to_SP(sender_id, order)
                        decline_sessions.pop(sender_id, None)
                    else:
                        await send_whatsapp_message(sender_id, "Order no longer available")
                    return

                if button_id == "language_yes":
                    await language_yes_message(sender_id)
                    return
                if button_id == "language_no":
                    await language_no_message(sender_id)
                    return
                if button_id == "language_phrase":
                    response = await language_lesson_response(query="Hi", user_id=sender_id)
                    await send_whatsapp_message(recipient_id=sender_id, message=response)
                    return

                if button_id == "menu_button":
                    api_url = f"{settings.BASE_URL}/main_design"
                    menu_data = await fetch_menu_data(api_url, "Main Menu")
                    if menu_data:
                        print(f"🔍 DEBUG - menu_data type: {type(menu_data)}")
                        print(f"🔍 DEBUG - menu_data content: {menu_data}")
                        if isinstance(menu_data, list):
                            menu_data = {"data": menu_data}
                        await send_whatsapp_menu_list_message(recipient_id=sender_id, card_data=menu_data)
                    return

                if button_id == "chat_button":
                    await send_whatsapp_message(
                        sender_id,
                        "💬 You can now chat with us! Just send your message and we'll be happy to help you with anything you need during your stay in Bali."
                    )
                    # Task 20: Flag support activation
                    asyncio.create_task(log_guest_inquiry(
                        sender_id,
                        user_villa_code or "WEB_VILLA_01",
                        "CLICKED: Chat with Us",
                        "Assigned to Support",
                        intent="support_request"
                    ))
                    return

                if category_text in ["✅ Accept", "❌ Decline"]:
                    if category_text == "✅ Accept":
                        order_num = message_payload["interactive"]["button_reply"]["id"]
                        service_provider_code = await get_service_provider_by_whatsapp(sender_id)
                        await order_collection.update_one(
                            {"order_number": order_num},
                            {"$set": {"service_provider_code": service_provider_code}}
                        )
                        local_order_store[sender_id] = order_num
                        session_id = await get_sender_id_by_order(order_num)

                        if session_id in website_sessions:
                            confirmation = await check_order_confirmation(order_num)
                            if confirmation == False:
                                await send_confirmation_order_to_SP(sender_id, order_num)
                            elif confirmation == True:
                                await send_whatsapp_message(sender_id, "Thank you for the acceptance.Unfortunately, this order has already been booked.")
                        else:
                            order_num = message_payload["interactive"]["button_reply"]["id"]
                            order_sessions[sender_id] = order_num
                            confirmation = await check_order_confirmation(order_num)
                            if confirmation == False:
                                await send_confirmation_order_to_SP(sender_id, order_num)
                            elif confirmation == True:
                                await send_whatsapp_message(sender_id, "Thank you for the acceptance.Unfortunately, this order has already been booked.")
                    elif category_text == "❌ Decline":
                        if button_id.startswith("decline_"):
                            order_num = button_id.split("_", 1)[1]
                            decline_sessions[sender_id] = order_num
                            await send_decline_confirmation(sender_id, order_num)
                        else:
                            await send_whatsapp_message(sender_id, "Invalid decline request.")
                        return

                elif category_text == "Yes":
                    logger.info("order number received")
                    if button_id.startswith("yes_order_"):
                        order_num = button_id.split("_", 2)[2]
                    else:
                        order_num = local_order_store.get(sender_id)
                    
                    logger.info(f"Order number for confirmation: {order_num}")
                    if order_num:
                        service_provider_code = await get_service_provider_by_whatsapp(sender_id)
                        
                        # [BUGFIX]: Atomic check to prevent race conditions. Only update if NOT already confirmed.
                        updated_order = await order_collection.find_one_and_update(
                            {
                                "order_number": order_num,
                                "confirmed_by_provider": {"$exists": False} # Or null, depending on schema, $exists is safer initially
                            },
                            {
                                "$set": {
                                    "confirmed_by_provider": sender_id,
                                    "confirmed_at": datetime.datetime.now(),
                                    "service_provider_code": service_provider_code
                                }
                            },
                            return_document=True
                        )

                        if not updated_order:
                            # It was already claimed or doesn't exist.
                            already_claimed = await order_collection.find_one({"order_number": order_num})
                            if already_claimed and already_claimed.get("confirmed_by_provider"):
                                await send_whatsapp_message(
                                    sender_id, 
                                    "⚠️ *Oops! Too late.*\n\nThis booking has already been claimed by another service provider. Thank you for your swift response, better luck next time!"
                                )
                            else:
                                await send_whatsapp_message(sender_id, "Order not found or an error occurred.")
                            
                            order_sessions.pop(sender_id, None)
                            return
                        user_sender_id = await update_order_confirmation(order_num, True)
                        print(user_sender_id)
                        order_data = await order_collection.find_one({"order_number": order_num})
                        if not order_data:
                            await send_whatsapp_message(sender_id, "Order not found.")
                            return
                        try:
                            order = Order(**order_data)
                        except Exception as e:
                            print(f"Error creating Order model: {e}")
                            await send_whatsapp_message(sender_id, "Error processing order.")
                            return
                        payment_result = await create_xendit_payment_with_distribution(order)
                        logger.info(f"payment result : {payment_result}")

                        if payment_result['success']:
                            await update_order_with_payment_info(order_num, payment_result)

                            # Notify customer that their service request has been accepted
                            acceptance_message = (
                                f"✅ *Great news!* A service provider has accepted your booking request!\n\n"
                                f"*Order ID:* {order_num}\n"
                                f"*Service:* {order_data.get('service_name', 'Your Service')}\n\n"
                                f"Please complete your payment using the secure link below to confirm your booking."
                            )
                            if user_sender_id.isdigit():
                                await send_whatsapp_message(user_sender_id, acceptance_message)

                            if user_sender_id.isdigit():
                                await send_interactive_message(user_sender_id, payment_result)
                            else:
                                payment_message = f"""🌴 ***Your Order Awaits!***\nThank you for choosing EASY Bali.\nPlease confirm your **order** by completing the payment through the secure link below.\nOnce payment is confirmed, we'll take care of the rest — just sit back, relax, and your service will come to you as scheduled."""

                                await manager.send_personal_message(
                                    message=f"{payment_message}\n[link]({payment_result['payment_url']})",
                                    session_id=user_sender_id,
                                    message_type="link_message"
                                )
                        else:
                            error_detail = payment_result.get('error', 'Unknown Error')
                            error_message = f"⚠️ *Payment System Issue*\n\nSorry, we encountered an issue creating your secure payment link:\n_{error_detail}_\n\nPlease try again or contact support."
                            if user_sender_id.isdigit():
                                await send_whatsapp_message(user_sender_id, error_message)
                            else:
                                await manager.send_personal_message(message=error_message, session_id=user_sender_id, message_type="error")

                        await send_whatsapp_message(
                            sender_id,
                            "You've successfully confirmed the booking! The guest has been sent a payment link. "
                            "You'll receive final confirmation once the payment is completed."
                        )
                        order_sessions.pop(sender_id, None)
                    else:
                        await send_whatsapp_message(sender_id, "No order found for confirmation.")

                elif category_text == "No":
                    order_sessions.pop(sender_id, None)
                    await send_whatsapp_message(sender_id, "Order cancelled.")

                category_id = message_payload["interactive"]["button_reply"]["id"]
                service_name = category_id.replace("_", " ")

            elif interactive_type == "list_reply":
                list_reply = message_payload["interactive"]["list_reply"]
                serviceitems_text = list_reply["title"]
                selected_id = list_reply["id"]

                # 1. Handle Categorized Selection (from Main Menu)
                # Categories from Main Menu use snake_case IDs. We'll use them to fetch subcategories.
                if not selected_id.startswith(("ai_service_", "subcat_", "service_")):
                    # Fetch subcategories for this category
                    category_title = serviceitems_text
                    api_url = f"{settings.BASE_URL}/categories/sections"
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(api_url, json={"category_title": category_title})
                            if response.status_code == 200:
                                subcat_data = response.json().get("subcategories", [])
                                await send_whatsapp_subcategory_list_message(sender_id, subcat_data, category_title)
                                return
                    except Exception as e:
                        print(f"Error fetching subcategories: {e}")

                # 2. Handle Subcategory Selection (leads to Service Items list)
                elif selected_id.startswith("subcat_"):
                    subcategory_title = serviceitems_text
                    api_url = f"{settings.BASE_URL}/sub_category/service_items"
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(api_url, json={"subcategory_title": subcategory_title})
                            if response.status_code == 200:
                                service_items = response.json().get("serviceitems", [])
                                await send_whatsapp_service_list_message(sender_id, service_items, subcategory_title)
                                return
                    except Exception as e:
                        print(f"Error fetching service items: {e}")

                # 3. Handle Service Item Selection (triggers 'Book Now' Flow)
                elif selected_id.startswith("service_"):
                    service_name = serviceitems_text
                    # Check if AI data exists for image/description
                    service_details = await ai_menu_generator.get_service_details_by_id(selected_id)
                    if service_details and service_details.get("image_url"):
                         await send_whatsapp_image_with_caption(
                            sender_id, 
                            service_details["image_url"], 
                            f"✨ *{service_name}*\n\n{service_details.get('description', '')[:200]}"
                        )
                    
                    # Direct to Booking Flow
                    token = f"book_{sender_id}_{service_name}"
                    await send_whatsapp_order_flow_message(sender_id, token)
                    return

                # 4. Handle AI-generated menu (Legacy/Search flow)
                elif selected_id.startswith("ai_service_"):
                    # Get full service details
                    service_details = await ai_menu_generator.get_service_details_by_id(selected_id)
                    
                    if service_details:
                        service_name = service_details["service_name"]
                        description = service_details["description"]
                        price = service_details["price"]
                        locations = service_details["locations"]
                        image_url = service_details["image_url"]
                        
                        # Send image if available
                        if image_url:
                            try:
                                await send_whatsapp_image_with_caption(
                                    sender_id,
                                    image_url,
                                    f"✨ *{service_name}*\n\n{description[:200]}"
                                )
                            except Exception as e:
                                print(f"Error sending image: {e}")
                        
                        # Format price properly
                        try:
                            price_num = int(str(price).replace(' ', '').replace(',', ''))
                            price_formatted = f"IDR {price_num:,}"
                        except:
                            price_formatted = f"IDR {price}"
                        
                        # Send booking prompt
                        booking_message = (
                            f"💰 *Price:* {price_formatted}\n"
                            f"📍 *Available in:* {locations}\n\n"
                            f"Would you like to book this service? Use the button below to continue 👇"
                        )
                        await send_whatsapp_message(sender_id, booking_message)
                        
                        # Send booking flow
                        token = f"book_{sender_id}_{service_name}"
                        await send_whatsapp_order_flow_message(sender_id, token)
                        return
                    else:
                        await send_whatsapp_message(
                            sender_id, 
                            "Sorry, I couldn't find the details for this service. Please try again or select another option."
                        )
                        return

            elif interactive_type == "nfm_reply": # This is the type for Flow replies
                nfm_reply = message_payload["interactive"]["nfm_reply"] # Corrected path to nfm_reply
                response_json_str = nfm_reply.get("response_json", "{}") # Get the JSON string

                try:
                    response_data = json.loads(response_json_str) # Parse the JSON string into a dictionary
                except json.JSONDecodeError as e:
                    print(f"❌ Error decoding NFM reply JSON: {e}")
                    await send_whatsapp_message(sender_id, "Sorry, there was an issue processing your selection. Please try again.")
                    return

                flow_token = response_data.get("flow_token")
                selected_service = response_data.get("selected_service")
                selected_date = response_data.get("selected_date")
                person_selection = response_data.get("person_selection")
                time_selection = response_data.get("time_selection")

                print(f"📋 Flow response - Token: {flow_token}")
                print(f"🛎️ Service: {selected_service}")
                print(f"📅 Date: {selected_date}")
                print(f"👥 Persons: {person_selection}")
                print(f"⏰ Time: {time_selection}")
                print(f"📋 Full response: {response_data}")

                if flow_token and selected_service and selected_date:
                    # Use sane defaults for optional fields to prevent silent booking drops
                    person_selection = person_selection or "1"
                    time_selection = time_selection or "Flexible"
                    try:
                        # Robust Date Parsing
                        try:
                            user_date = dateutil.parser.parse(str(selected_date))
                        except (ValueError, TypeError):
                            print(f"❌ Failed to parse date '{selected_date}', using current date")
                            user_date = datetime.datetime.now()

                        # Reconstruct the original service name from the AI flow ID
                        # Handles 'ai_service_N_Name_With_Underscores'
                        if str(selected_service).startswith("ai_service_"):
                            parts = str(selected_service).split("_", 3)
                            if len(parts) >= 4:
                                selected_service = parts[3].replace('_', ' ')
                        
                        logger.info(f"✨ Booking flow processing: Service='{selected_service}', Date='{user_date}', Persons='{person_selection}'")

                        base_price = await get_service_base_price(selected_service)

                        new_order = await initiate_chat_session(
                            sender_id=sender_id,
                            service_name=selected_service, 
                            person_count=person_selection,
                            base_price=base_price,
                            date=user_date,
                            time=time_selection
                        )
                        new_order.date = user_date
                        new_order.time = time_selection
                        new_order.status = "pending_confirmation"
                        
                        # Save the completed order to database
                        await save_order_to_db(new_order.dict())
                        logger.info(f"🛎️ Order {new_order.order_number} created - waiting for SP confirmation")

                        # Clean price — strip EVERYTHING non-numeric (handles \xa0, commas, spaces from Google Sheets)
                        try:
                            price_cleaned = int(re.sub(r'[^\d]', '', str(new_order.price)) or '0')
                            price_display = f"IDR {price_cleaned:,}"
                        except Exception:
                            price_display = f"IDR {new_order.price}"

                        confirmation_message = (
                            f"✨ *Booking Request Received!* ✨\n\n"
                            f"*Order ID:* {new_order.order_number}\n"
                            f"*Service:* {new_order.service_name}\n"
                            f"*Date:* {new_order.date.strftime('%d-%m-%Y')}\n"
                            f"*Time:* {new_order.time}\n"
                            f"*Total Price:* {price_display}\n\n"
                            "Our service providers have been notified. We will send you a secure payment link as soon as a provider confirms their availability!"
                        )

                        await send_whatsapp_message(sender_id, confirmation_message)

                        # Parallel: Notify Service Providers
                        service_numbers = await fetch_whatsapp_numbers(new_order.service_name)

                        # [TESTING]: Hardcoded test SP - Clarence (remove after testing is complete)
                        test_sp_num = "6281999281660"
                        if test_sp_num not in service_numbers:
                            service_numbers.append(test_sp_num)

                        logger.info(f"🚀 Notifying {len(service_numbers)} numbers: {service_numbers}")
                        for num in service_numbers:
                            try:
                                await send_whatsapp_order_to_SP(num, new_order.dict())
                            except Exception as e:
                                logger.error(f"Failed to notify {num}: {e}")
                        
                        return
                        
                    except Exception as booking_err:
                        import traceback
                        logger.error(f"❌ Booking flow error: {booking_err}\n{traceback.format_exc()}")
                        await send_whatsapp_message(
                            sender_id,
                            "Sorry, we encountered an issue processing your booking. Please try again or type *menu* to start over."
                        )
                        return
                else:
                    # Missing critical booking fields — inform user clearly
                    logger.error(f"❌ NFM reply missing fields: flow_token={flow_token}, service={selected_service}, date={selected_date}")
                    await send_whatsapp_message(
                        sender_id,
                        "⚠️ We couldn't complete your booking — some details were missing from the form. "
                        "Please try again by typing *Order Services* or selecting from the menu."
                    )
                    return
        

        if message_text and re.search(r"Hi,?\s*I\s*am\s*in", message_text, re.IGNORECASE):    
            try:
                villa_name = extract_villa_name (message_text)
                villa_code = await get_villa_code_by_name(villa_name)
                
                if villa_code:
                    success = await save_user_villa_code(sender_id, villa_code)
                    if success:
                        await perform_arrival_confirmation(sender_id, villa_code)
                        await starting_message(sender_id)
                        return
                    else:
                        await send_whatsapp_message(
                            sender_id,
                            "❌ Sorry, there was an error setting up your villa access. Please try the link again."
                        )
                        return
                else:
                    # Villa name not found in database mapping
                    await send_whatsapp_message(
                        sender_id,
                        f"❌ *Villa '{villa_name}' not recognized.*\n\n"
                        "Please ensure you are using the correct link provided in your villa, or contact support if the issue persists."
                    )
                    return
                    
            except Exception as e:
                print(f"Error processing villa initialization: {e}")
                await send_whatsapp_message(
                    sender_id,
                    "❌ There was an error processing your request. Please try again."
                )
                return

        user_villa_code = await get_user_villa_code(sender_id)

        # If user doesn't have villa code and is not in villa_code_sessions
        if not user_villa_code and sender_id not in villa_code_sessions:
            if message_text and message_text.lower() in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "hey there", "hi there", "hello there", "howdy", "what's up?", "how are you?", "how's it going?", "nice to meet you", "long time no see", "yo", "greetings", "how have you been?", "good to see you", "welcome"]:
                villa_code_sessions[sender_id] = True
                await send_villa_code_request(sender_id)
                return
            # If it's any other message and no villa code, still ask for villa code
            elif message_text:
                villa_code_sessions[sender_id] = True
                await send_villa_code_request(sender_id)
                return
        if sender_id in villa_code_sessions and message_text:
            villa_code = message_text.strip().upper()

            if is_valid_villa_code(villa_code):
                success = await save_user_villa_code(sender_id, villa_code)
                if success:
                    villa_code_sessions.pop(sender_id, None)
                    await send_whatsapp_message(
                        sender_id,
                        f"✅ Villa Code {villa_code} registered successfully!"
                    )
                    await starting_message(sender_id)
                    return
                else:
                    await send_whatsapp_message(
                        sender_id,
                        "❌ Sorry, there was an error saving your Villa Code. Please try again."
                    )
                    return
            else:
                await send_whatsapp_message(
                    sender_id,
                    "❌ Invalid Villa Code format. Please enter a valid Villa Code (e.g., V1, V2, V3):"
                )
                return

        if user_villa_code:
            # Task 22: Active Issue Reporting Session
            if sender_id in issue_reporting_sessions:
                if message_text == "CANCEL":
                    issue_reporting_sessions.pop(sender_id, None)
                    await send_whatsapp_message(sender_id, "Issue reporting cancelled.")
                    await starting_message(sender_id)
                    return
                
                # Logic to process text, image, or voice note as an issue
                media_id = None
                media_type = "text"
                if "image" in message_payload:
                    media_id = message_payload["image"]["id"]
                    media_type = "image"
                elif "audio" in message_payload:
                    media_id = message_payload["audio"]["id"]
                    media_type = "voice_note"
                
                # Log the issue
                issue_data = {
                    "sender_id": sender_id,
                    "villa_code": user_villa_code,
                    "description": message_text if media_type == "text" else f"Media issue: {media_type}",
                    "media_id": media_id,
                    "media_type": media_type,
                    "timestamp": datetime.datetime.now(),
                    "status": "pending"
                }
                await issue_collection.insert_one(issue_data)
                
                # Notify Villa Manager
                villa_info = await get_villa_info_by_code(user_villa_code)
                if villa_info and villa_info.get("manager_number"):
                    mgr_num = "".join(filter(str.isdigit, str(villa_info["manager_number"])))
                    mgr_msg = (
                        f"🚨 *New Issue Reported!*\n\n"
                        f"Villa: *{villa_info.get('name')}* ({user_villa_code})\n"
                        f"Guest ID: `{sender_id[-4:]}`\n"
                        f"Issue: {issue_data['description']}\n"
                        f"Type: {media_type.capitalize()}"
                    )
                    await send_whatsapp_message(mgr_num, mgr_msg)
                
                issue_reporting_sessions.pop(sender_id, None)
                await send_whatsapp_message(
                    sender_id,
                    "✅ *Issue Received*\n\n"
                    "Thank you for reporting this. Our team and the villa manager have been notified and will address this as soon as possible."
                )
                return

            if message_text and message_text.lower() in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "hey there", "hi there", "hello there", "howdy", "what's up?", "how are you?", "how's it going?", "yo", "greetings", "bonjour"]:
                await starting_message(sender_id)
                return

            # Task 22: Issue Reporting Detection
            if message_text and any(word in message_text.lower() for word in ["issue", "problem", "report", "broken", "not working", "complain", "help me"]):
                issue_reporting_sessions[sender_id] = {"step": "awaiting_description", "timestamp": datetime.datetime.now()}
                await send_whatsapp_message(
                    sender_id,
                    "⚠️ *Issue Reporting Mode*\n\n"
                    "I'm sorry to hear you're experiencing an issue. Please describe the problem in detail.\n\n"
                    "You can also send a **Photo** or **Voice Note** to help us understand the situation better. 📸 🎤"
                )
                return

            if message_text and sender_id in persistent_mode_sessions and not serviceitems_text and not category_text:
                mode = persistent_mode_sessions.get(sender_id)
                if mode:
                    mode_info = PERSISTENT_API_MAPPING.get(mode)
                    if mode_info:
                        query_to_send = message_text
                        data = await mode_info["fetch_func"](mode_info["url"], query=query_to_send, user_id=sender_id)
                        if not data:
                            await send_whatsapp_message(sender_id, f"Sorry, no data available for {mode} at this time.")
                        else:
                            await send_whatsapp_message(sender_id, data)
                    return

            if selected_id in PERSISTENT_API_MAPPING:
                persistent_mode_sessions[sender_id] = selected_id
                mode_info = PERSISTENT_API_MAPPING.get(selected_id)
                if mode_info:
                    data = await mode_info["fetch_func"](mode_info["url"], query="Hi", user_id=sender_id)
                    if not data:
                        await send_whatsapp_message(sender_id, f"Sorry, no data available for {serviceitems_text} at this time.")
                    else:
                        await send_whatsapp_message(sender_id, data)
                return
            
            elif selected_id == "language_lesson":
                    language_lesson_sessions[sender_id] = True
                    await language_starting_message(sender_id)
                    return

            if sender_id in language_lesson_sessions:
                if message_text:
                    ai_response = await language_lesson_response(user_id=sender_id, query=message_text)
                    await send_whatsapp_message(sender_id, ai_response)
                    return
                else:
                    language_lesson_sessions.pop(sender_id, None)

            # Your existing menu mapping logic
            menu_mapping = {
                "Menu": "Main Menu",
                "menu": "Main Menu",
                "main menu": "Main Menu",
                "category": "Category",
                "show category": "Category",
                "show menu": "Main Menu",
                "🔙 Main Menu": "Main Menu"
            }

            if category_text in menu_mapping:
                api_url = f"{settings.BASE_URL}/main_design"
                menu_data = await fetch_menu_data(api_url, "Main Menu")
                if menu_data:
                    if isinstance(menu_data, list):
                        menu_data = {"data": menu_data}
                    await send_whatsapp_menu_list_message(recipient_id=sender_id, card_data=menu_data)
                return

            elif serviceitems_text:
                if serviceitems_text == "Order Services":
                    token = f"order{sender_id}"
                    await send_whatsapp_order_flow_message(sender_id, flow_token=token)
                    return
                elif serviceitems_text in ["Local Guide", "Recommendations", "Discount & Promotions"]:
                    main_design = await fetch_menu_design(serviceitems_text)
                    if not main_design:
                        await send_whatsapp_message(sender_id, "Sorry, we couldn't fetch the menu design at this time.")
                        return
                    await send_whatsapp_main_menu_list_message(sender_id, main_design)
                    return

                elif category_text == "Read Safety Tips":
                    link = "https://www.canva.com/design/DAGaNLT8Owc/gDSbEepIXK4OJxdOOtx92Q/view?utm_content=DAGaNLT8Owc&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h3bad98561a"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Find Medical Help":
                    link= "https://www.canva.com/design/DAGbfiNdbTw/rJdf8dxswAQDXZf3XtPSqw/view?utm_content=DAGbfiNdbTw&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h17b7214f43"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Know the Local Rules":
                    link = "https://www.canva.com/design/DAGbZYkN0V8/SRJA3kOkFPzFqRmJEjlGbQ/view?utm_content=DAGbZYkN0V8&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h1d8411966d"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Shop the Best Places":
                    link = "https://maps.app.goo.gl/soEShhHPXVJhM5ms6"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Find Your Spot":
                    link = "https://maps.app.goo.gl/YvPCmHqJTh2ZNz3HA"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Relax & Recharge":
                    link = "https://maps.app.goo.gl/26FqxqXMmgvdyXvRA"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Explore After Dark":
                    link = "https://maps.app.goo.gl/NcKZhc3vRUeqKF6M7"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return
                elif category_text == "Locate Hospital":
                    link = "https://maps.app.goo.gl/SVWEZTNwhZUjPpZR6"
                    await send_whatsapp_interactive_link(sender_id, link)
                    return

                elif category_text in ["Find Dining Options", "Discover Spots"]:
                    main_design = await fetch_menu_design(service_name)
                    if not main_design:
                        await send_whatsapp_message(sender_id, "Sorry, we couldn't fetch the menu design at this time.")
                        return
                    for subcard_data in main_design:
                        await send_whatsapp_card_with_link(sender_id, subcard_data)
                    return

                else:
                    api_url = settings.BASE_URL
                    serviceitem_data = await fetch_service_items(api_url, serviceitems_text)

                    if not serviceitem_data:
                        print("DEBUG: No submenu data received!")
                        await send_whatsapp_message(sender_id, "Sorry, we couldn't fetch the categories at this time.")
                        return

                    for subcard_data in serviceitem_data:
                        await send_whatsapp_card(sender_id, subcard_data)
                    return

            else:
                if message_text:
                    ai_result = await whatsapp_response(message_text, sender_id, user_villa_code or "WEB_VILLA_01")

                    print(ai_result)
                    
                    if ai_result:
                        # Send menu if available
                        if ai_result.get("should_send_menu") and ai_result.get("menu_data"):
                            await send_ai_whatsapp_order_flow_message(
                                sender_id,
                                flow_token="hkjhkhkjhkhkjhkjhkjk",
                                menu_data=ai_result.get("menu_data"),
                            )
                        else:
                            # Only send text message if there's no menu
                            await send_whatsapp_message(sender_id, ai_result["text"])
                            
                            # Task 19: Log Inquiry for Tracking
                            asyncio.create_task(log_guest_inquiry(
                                sender_id, 
                                user_villa_code or "WEB_VILLA_01",
                                message_text,
                                ai_result["text"]
                            ))
                    else:
                        await send_whatsapp_message(
                            sender_id, 
                            "Sorry, I'm having trouble processing your message. Reply with 'Hi' to see the menu."
                        )
    except Exception as e:
        print(f"Error processing message from {sender_id}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        end_time = datetime.datetime.now()
        latency = (end_time - start_time).total_seconds()
        logger.info(f"⏱️ Finished processing message {message_id}. Latency: {latency:.2f}s")
        # Log latency to DB for monitoring
        try:
            from app.db.session import db
            await db["analytics_latency"].insert_one({
                "message_id": message_id,
                "sender_id": sender_id,
                "latency_seconds": latency,
                "timestamp": datetime.datetime.utcnow()
            })
        except:
            pass



async def send_whatsapp_message(recipient_id: str, message: str):
    """
    Send a simple text message to WhatsApp.
    """
    try:
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "text": {"body": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            if response.status_code >= 400:
                 logger.error(f"❌ WhatsApp API Error (send_whatsapp_message): Status {response.status_code}, Body: {response.text}")
            response.raise_for_status()
    except Exception as e:
        print(f" Error sending WhatsApp message: {e}")


# async def notify_payment_completion(order_data: dict):
#     try:
#         sender_id = order_data.get("sender_id")
#         order_number = order_data.get("order_number")
#         service_name = order_data.get("service_name")
#         if sender_id:
#             completion_message = (
#                 f"✅ Payment Confirmed!\n\n"
#                 f"Order {order_number} for {service_name} has been paid successfully. "
#                 f"The service provider has been notified and will contact you shortly."
#             )
#             await send_whatsapp_message(sender_id, completion_message)
#         service_provider_code = order_data.get("confirmed_by_provider")
#         if service_provider_code:
#             provider_message = (
#                 f"💰 Payment Received!\n\n"
#                 f"Order {order_number} has been paid. Please proceed with the service delivery."
#             )
#             await send_whatsapp_message(service_provider_code, provider_message)
            
#     except Exception as e:
#         print(f"Notification error: {str(e)}")


async def notify_payment_completion(order_data: dict):
    try:
        sender_id = order_data.get("sender_id")
        order_number = order_data.get("order_number")
        service_name = order_data.get("service_name")
        price = order_data.get("price")
        villa_code = order_data.get("villa_code")
        
        if not sender_id:
            logger.warning(f"No sender_id found for order {order_number}")
            return
        
        # Determine connection type
        is_whatsapp = sender_id.isdigit()
        is_websocket = not is_whatsapp
        
        # 1. Notify Customer
        completion_message = (
            f"🌟 ***Booking Confirmed & Paid!*** 🌟\n\n"
            f"Hi! We've successfully received your payment for your **{service_name}** (Order: {order_number}).\n\n"
            f"Our service provider has been notified and will coordinate final details with you shortly. "
            f"Thank you for choosing EASY Bali! 🌴"
        )
        if is_whatsapp:
            await send_whatsapp_message(sender_id, completion_message)
        elif is_websocket:
            await manager.send_personal_message(
                message=completion_message,
                session_id=sender_id,
                message_type="payment_confirmed"
            )
            
        # 2. Notify Service Provider
        await notify_service_provider(order_data)
        
        # 3. Notify Villa
        if villa_code:
            villa_number = await get_villa_whatsapp_by_code(villa_code)
            if villa_number:
                villa_msg = (
                    f"🛎️ ***Guest Payment Made!***\n\n"
                    f"A guest in your villa ({villa_code}) has just paid for **{service_name}**.\n"
                    f"**Order ID:** {order_number}\n"
                    f"**Amount:** IDR {int(float(price)):,}\n\n"
                    f"Service is scheduled as confirmed! ✅"
                )
                await send_whatsapp_message(villa_number, villa_msg)
        
        # 4. Notify Easy-Bali Admin
        await notify_admin_of_outcome(order_data, "SUCCESS")
        
    except Exception as e:
        logger.error(f"Notification error in notify_payment_completion: {str(e)}")
        import traceback
        traceback.print_exc()

async def notify_payment_failure(order_data: dict, reason: str):
    """Notify relevant parties about payment failure/expiry."""
    try:
        await notify_admin_of_outcome(order_data, f"FAILURE: {reason}")
    except Exception as e:
        logger.error(f"Error in notify_payment_failure: {e}")

async def notify_admin_of_outcome(order_data: dict, outcome: str):
    """Unified admin notification for booking outcomes."""
    try:
        order_number = order_data.get("order_number")
        service_name = order_data.get("service_name")
        price = order_data.get("price")
        villa_code = order_data.get("villa_code")
        admin_number = os.getenv("ADMIN_WHATSAPP_NUMBER", "62895627705139")

        if outcome == "SUCCESS":
            emoji = "💰"
            title = "REVENUE ALERT!"
            status_text = "Payment confirmed"
        else:
            emoji = "⚠️"
            title = "BOOKING ALERT (ACTION MAY BE NEEDED)"
            status_text = f"Payment {outcome}"

        admin_msg = (
            f"{emoji} ***{title}*** {emoji}\n\n"
            f"**Order:** {order_number}\n"
            f"**Status:** {status_text}\n"
            f"**Service:** {service_name}\n"
            f"**Villa:** {villa_code}\n"
            f"**Amount:** IDR {int(float(price)):,}\n\n"
            f"Check Dashboard: {settings.BASE_URL}/admin/dashboard"
        )
        await send_whatsapp_message(admin_number, admin_msg)
        
        # Placeholder for real email if needed in future
        logger.info(f"📧 Admin Notification (Email Simulated) for Order {order_number}: {status_text}")
        
    except Exception as e:
        logger.error(f"Admin notification error: {e}")

async def send_invoice_and_handle_closure(order_data: dict, invoice_result: dict, is_whatsapp: bool, is_websocket: bool):
    try:
        sender_id = order_data['sender_id']
        order_number = order_data['order_number']
        download_url = invoice_result['download_url']
        
        if is_whatsapp:
            await send_invoice_with_download(sender_id, download_url, order_number)
            
        elif is_websocket:
            invoice_message = (
                f"✅ ***Receipt Generated!***\n"
                f"Order **{order_number}** for {order_data['service_name']} has been confirmed and paid.\n"
                f"Please save your receipt for your records.\n"
                f"**Download your official receipt:**\n"
                f"[link]({download_url})\n\n"
                f"Thank you for choosing EASY Bali! 🌴"
            )
            
            await manager.send_personal_message(
                message=invoice_message,
                session_id=sender_id,
                message_type="invoice_download"
            )
            await asyncio.sleep(0.5)
            await manager.send_personal_message(
                message="",
                session_id=sender_id,
                message_type="destroy"
            )
            
            logger.info(f"✅ WebSocket connection closed for session: {sender_id}")
            
    except Exception as e:
        logger.exception(f"Invoice sending error: {str(e)}")
        if is_websocket:
            try:
                await manager.send_personal_message(
                    message="",
                    session_id=sender_id,
                    message_type="destroy"
                )
            except Exception as cleanup_error:
                logger.exception(f"WebSocket cleanup error: {cleanup_error}")

async def notify_service_provider(order_data: dict):
    try:
        service_provider_number = order_data.get("confirmed_by_provider")
        order_number = order_data.get("order_number")
        service_name = order_data.get("service_name")
        appointment_date = order_data.get("date")
        appointment_time = order_data.get("time")
        villa_code = order_data.get("villa_code")

        # Format date for readability
        date_str = "N/A"
        if appointment_date:
            if hasattr(appointment_date, "strftime"):
                date_str = appointment_date.strftime("%d %B %Y")
            else:
                date_str = str(appointment_date)

        logger.info(f"SP payment notification: order={order_number}, sp_number={service_provider_number}")
        if service_provider_number:
            provider_message = (
                f"🎉 ***Congratulations!*** 🎉\n\n"
                f"The customer has paid for the service which you accepted. Kindly provide the accepted service.\n\n"
                f"📌 ***Order Details:***\n"
                f"• **Order #:** {order_number}\n"
                f"• **Service:** {service_name}\n"
                f"• **Date:** {date_str}\n"
                f"• **Time:** {appointment_time or 'As scheduled'}\n"
                f"• **Villa:** {villa_code or 'N/A'}\n"
                f"• **Status:** PAID ✅\n\n"
                f"Please coordinate directly to ensure a smooth delivery. Thank you for your professional service!"
            )
            await send_whatsapp_message(service_provider_number, provider_message)
            
    except Exception as e:
        logger.error(f"Service provider notification error in notify_service_provider: {str(e)}")

async def get_villa_whatsapp_by_code(villa_code: str) -> str:
    from app.services.menu_services import cache
    try:
        villas_df = cache.get("villas_data")
        if villas_df is not None and not villas_df.empty:
            # Try to find a column that looks like WhatsApp or Phone
            cols = villas_df.columns.tolist()
            wa_col = next((c for c in cols if "whatsapp" in c.lower() or "phone" in c.lower() or "number" in c.lower() and c != "Number"), None)
            
            if not wa_col:
                # Fallback to predefined mapping if any, or column index
                return None
                
            match = villas_df[villas_df["Number"] == villa_code]
            if not match.empty:
                val = str(match.iloc[0][wa_col])
                if val and val != "nan":
                    # Clean number: ensure it has country code, no + or spaces
                    clean = re.sub(r'[^\d]', '', val)
                    return clean
        return None
    except Exception as e:
        logger.error(f"Error fetching villa whatsapp: {e}")
        return None
