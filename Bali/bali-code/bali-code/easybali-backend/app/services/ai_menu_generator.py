# app/services/ai_menu_generator.py
from typing import Dict, List, Optional, Any
import re
import json
from app.services.menu_services import cache
from app.services.openai_client import client
from app.settings.config import settings

class AIMenuGenerator:
    """Generate dynamic WhatsApp menus based on AI-detected intent using Google Sheets data"""
    
    def __init__(self):
        # ═══════════════════════════════════════════════════════════════
        # SUBCATEGORY IMAGE URLS - Maps subcategory to S3 image URL
        # ═══════════════════════════════════════════════════════════════
        self.subcategory_image_urls = {
            "Airport Pickup/Drop": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Airport_Pickup_Drop.jpg",
            "Boxing": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Boxing.jpg",
            "Equipment Rental": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Equipment_Rental.jpg",
            "Fast Boat": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Fast_Boat.jpg",
            "Flowers": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Flowers.jpg",
            "Helicopter Ride": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Helicopter_Ride.jpg",
            "IV Drip": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/IV_Drip.jpg",
            "In-House Dining": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/In_House_Dining.jpg",
            "Island Tour": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Island_Tour.jpg",
            "Kickboxing": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Kickboxing.jpg",
            "Laundry": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Laundry.jpg",
            "Massage": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Massage.jpg",
            "Movie Night": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Movie_Night.jpg",
            "Muay Thai": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Muay_Thai.jpg",
            "Photography": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Photography.jpg",
            "Physiotherapy": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Physiotherapy.jpg",
            "Private Barber": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Private_Barber.jpg",
            "Private Chef": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Private_Chef.jpg",
            "Shisha Rental": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Shisha_Rental.jpg",
            "Tour with Driver": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Tour_with_Driver.jpg",
            "Yoga": "https://easybali.s3.ap-southeast-2.amazonaws.com/services/Yoga.jpg"
        }
        
        self.service_categories = {
            "massage": {
                "category": "Health & Wellness",
                "subcategory": "Massage",
                "keywords": ["massage", "spa", "balinese", "aroma", "aromatherapy", "shiatsu", "reflexology", "facial", "body treatment"]
            },
            "yoga": {
                "category": "Health & Wellness",
                "subcategory": "Yoga",
                "keywords": ["yoga", "meditation", "mobility", "stretch", "pilates"]
            },
            "muay_thai": {
                "category": "Health & Wellness",
                "subcategory": "Muay Thai",
                "keywords": ["muay thai", "martial arts", "sparring", "thai boxing"]
            },
            "boxing": {
                "category": "Health & Wellness",
                "subcategory": "Boxing",
                "keywords": ["boxing", "fight", "punch"]
            },
            "kickboxing": {
                "category": "Health & Wellness",
                "subcategory": "Kickboxing",
                "keywords": ["kickboxing", "kick"]
            },
            "photography": {
                "category": "Services",
                "subcategory": "Photography",
                "keywords": ["photography", "photoshoot", "photographer", "photo", "camera", "video"]
            },
            "private_chef": {
                "category": "Dining",
                "subcategory": "Private Chef",
                "keywords": ["chef", "cook", "private chef", "bbq", "dinner"]
            },
            "iv_drip": {
                "category": "Health & Wellness",
                "subcategory": "IV Drip",
                "keywords": ["iv drip", "medical", "physiotherapy", "doctor", "vitamin", "hangover"]
            },
            "tour_driver": {
                "category": "Transportation",
                "subcategory": "Tour with Driver",
                "keywords": ["driver", "tour", "car", "van", "transport", "driver with car", "island tour"]
            },
            "helicopter": {
                "category": "Transportation",
                "subcategory": "Helicopter Ride",
                "keywords": ["helicopter", "heli", "chopper", "flight"]
            },
            "airport_transfer": {
                "category": "Transportation",
                "subcategory": "Airport Pickup/Drop",
                "keywords": ["airport", "pickup", "drop", "transfer", "arrival", "departure"]
            },
            "bike_rental": {
                "category": "Rental",
                "subcategory": "Bike Rental",
                "keywords": ["scooter", "bike", "nmax", "pcx", "scoopy", "motorcycle", "yamaha", "honda"]
            },
            "fast_boat": {
                "category": "Transportation",
                "subcategory": "Fast Boat",
                "keywords": ["boat", "fast boat", "gili", "nusa penida", "lembongan", "ferry"]
            },
            "flowers": {
                "category": "Services",
                "subcategory": "Flowers",
                "keywords": ["flowers", "bouquet", "floral", "anniversary", "birthday"]
            },
            "laundry": {
                "category": "Services",
                "subcategory": "Laundry",
                "keywords": ["laundry", "wash", "dry clean", "ironing"]
            }
        }
    
    async def intelligent_service_check(self, query: str) -> Dict[str, Any]:
        """Use AI to determine if user is requesting/discussing a specific service we offer."""
        
        our_services = []
        try:
            main_df = cache.get("main_menu_design")
            design_df = cache.get("design_df")
            
            if main_df is not None and not main_df.empty and design_df is not None and not design_df.empty:
                if "Menu Location" in main_df.columns and "Category" in design_df.columns:
                    valid_sections = main_df[main_df["Menu Location"].isin(["Services", "Rental", "Rentals", "Discount & Promotions", "Recommendation"])]
                    valid_cat_names = valid_sections["Title"].unique().tolist()
                    
                    if "Sub-category" in design_df.columns:
                        mask = design_df["Category"].isin(valid_cat_names)
                        relevant = design_df[mask]
                        for _, row in relevant.drop_duplicates(subset=["Sub-category"]).iterrows():
                            sub = row.get("Sub-category")
                            if sub:
                                our_services.append({"name": sub, "category": row.get("Category")})
        except Exception as cache_err:
            print(f"[intelligent_service_check] Cache read error (non-fatal): {cache_err}")

        # Always include core hardcoded services to ensure reliability for Martial Arts, Photography, etc.
        for _, info in self.service_categories.items():
            if not any(s['name'].lower() == info["subcategory"].lower() for s in our_services):
                our_services.append({"name": info["subcategory"], "category": info["category"]})
        
        services_list = "\n".join([f"- {s['name']} ({s['category']})" for s in our_services])
        
        prompt = f"""You are a Concierge Service Matcher.
        
AVAILABLE SERVICES:
{services_list}

USER QUERY: "{query}"

TASK:
1. Is this a request for a service, or providing details (dates/times) specifically for one of our services? 
   Note: Mentioning items like "Scoopy", "Scooter", "Massage", "NMAX", "Bike" counts as a service request.
2. Does it match our list above?

Return ONLY valid JSON:
{{{{
    "is_service_request": true/false,
    "requested_service": "name",
    "we_offer_it": true/false,
    "matched_service": "exact name from AVAILABLE SERVICES above",
    "confidence": float
}}}}
"""
        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a precise AI. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[intelligent_service_check] Error: {e}")
            return {"is_service_request": False, "we_offer_it": False}

    def detect_service_intent(self, query: str) -> Optional[Dict[str, str]]:
        """Detect which service category user is asking about using keywords"""
        query_lower = query.lower()
        scores = {}
        for service_type, info in self.service_categories.items():
            score = 0
            for keyword in info.get("keywords", []):
                if keyword in query_lower:
                    score += len(keyword.split())
            if score > 0:
                scores[service_type] = score
        
        if scores:
            service_type = max(scores.items(), key=lambda x: x[1])[0]
            info = self.service_categories[service_type]
            return {"service_type": service_type, "category": info["category"], "subcategory": info["subcategory"]}
        return None

    def extract_requirements(self, query: str) -> Dict[str, Any]:
        """Extract parameters like location, people, budget, time, date"""
        reqs = {"location": None, "people_count": None, "budget": None, "time_preference": None, "date": None}
        
        locations = ["canggu", "seminyak", "uluwatu", "ubud", "berawa", "umalas", "kerobokan"]
        for loc in locations:
            if loc in query.lower():
                reqs["location"] = loc.title()
                break
        
        match_pax = re.search(r'(\d+)\s*(?:people|person|pax|guests?)', query.lower())
        if match_pax: reqs["people_count"] = int(match_pax.group(1))

        match_budget = re.search(r'(?:max|budget)\s*(?:idr)?\s*(\d+(?:k|000)?)', query.lower())
        if match_budget: reqs["budget"] = int(match_budget.group(1).replace('k', '000'))
        
        if any(kw in query.lower() for kw in ["morning", "am"]): reqs["time_preference"] = "morning"
        elif any(kw in query.lower() for kw in ["afternoon", "noon"]): reqs["time_preference"] = "afternoon"
        elif any(kw in query.lower() for kw in ["evening", "night"]): reqs["time_preference"] = "evening"
        
        return reqs

    async def generate_service_menu(self, category: str, subcategory: Optional[str], requirements: Dict[str, Any], _villa_code: str = "WEB_VILLA_01") -> Optional[Dict[str, Any]]:
        """Filter services and create a structured menu for the web UI"""
        from app.services.google_sheets_service import google_sheets_service
        all_services = await google_sheets_service.get_services_data()
        if not all_services: return None
        
        filtered = []
        target_cat = category.lower().strip()
        for s in all_services:
            db_cat = s['category'].lower().strip()
            # Lenient category check (Rental vs Rentals)
            if db_cat != target_cat and db_cat != target_cat + 's' and db_cat + 's' != target_cat:
                if target_cat not in db_cat and db_cat not in target_cat:
                    continue
            
            if subcategory and s['subcategory'].lower() != subcategory.lower():
                continue
            
            if requirements.get("location"):
                loc = requirements["location"].lower()
                if loc not in s['villa_code'].lower() and s['villa_code'].lower() != 'all':
                    continue
            
            filtered.append(s)
            
        if not filtered: return None
            
        if requirements.get("budget"):
            budget = requirements["budget"]
            filtered = [s for s in filtered if int(re.sub(r'[^\d]', '', str(s.get('price', '0'))) or 0) <= budget]
            
        if not filtered: return None
        
        rows = []
        for idx, service in enumerate(filtered[:15]):
            name = service.get("service_name", "Unknown Service")
            
            # Use Final Price (Service Item Button) from sheet — only digits
            price_val = service.get("price", "")
            try:
                price_digits = re.sub(r'[^\d]', '', str(price_val))
                price_clean = f"{int(price_digits):,}".replace(',', '.') if price_digits and int(price_digits) > 0 else "0"
            except Exception:
                price_clean = "0"
            
            rows.append({
                "id": f"ai_service_{idx}_{name.replace(' ', '_')}",
                "title": name, # No truncation for Web UI
                "full_title": name,
                "description": service.get("description", "")[:72],
                "price": price_clean
            })
        
        img_url = self.subcategory_image_urls.get(subcategory) if subcategory else None
        
        return {
            "title": (subcategory or category)[:60],
            "description": f"Found {len(rows)} service(s) matching your request.",
            "image_url": img_url,
            "sections": [{"title": "Available Services", "rows": rows}]
        }

    async def get_service_details_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a service by its generated ID"""
        from app.services.google_sheets_service import google_sheets_service
        all_services = await google_sheets_service.get_services_data()
        if not all_services: return None
        
        parts = service_id.split("_")
        if len(parts) >= 3:
            s_name = "_".join(parts[2:]).replace('_', ' ').lower()
            for s in all_services:
                if s['service_name'].lower() == s_name:
                    return s
        return None

ai_menu_generator = AIMenuGenerator()