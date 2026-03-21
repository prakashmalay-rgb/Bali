import httpx
import logging

from fastapi import HTTPException
from app.settings.config import settings
from app.services.openai_client import client
from app.utils.chat_memory import get_conversation_history, trim_history, save_message

logger = logging.getLogger(__name__)


def _get_words() -> list:
    """Fetch language lesson words from the cache (AI Material sheet)."""
    try:
        from app.services.menu_services import get_language_lesson_words
        return get_language_lesson_words()
    except Exception as e:
        logger.warning(f"Could not load language lesson words from cache: {e}")
        return []


def _format_lesson_card(word_data: dict, index: int, total: int) -> str:
    english = str(word_data.get("English", "")).strip()
    indonesian = str(word_data.get("Indonesian", "")).strip()
    id_pron = str(word_data.get("Indonesian Pronunciation", "")).strip()
    balinese = str(word_data.get("Balinese", "")).strip()
    bal_pron = str(word_data.get("Balinese Pronunciation", "")).strip()
    context = str(word_data.get("Cultural Context", "")).strip()

    lines = [f"*{english}*  ({index + 1}/{total})", ""]
    if indonesian:
        lines.append(f"🇮🇩 Indonesian: {indonesian}")
        if id_pron:
            lines.append(f"   Pronunciation: {id_pron}")
    if balinese:
        lines.append(f"🌺 Balinese: {balinese}")
        if bal_pron:
            lines.append(f"   Pronunciation: {bal_pron}")
    lines.append(f"\nMeaning: {english}")
    if context:
        lines += [f"Example: {context}"]
    return "\n".join(lines)


async def _send_lesson_with_buttons(sender_id: str, body_text: str) -> None:
    """Send an interactive button message with ✅ Yes / ❌ No for lesson cycling."""
    headers = {
        "Authorization": f"Bearer {settings.access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": sender_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "language_yes", "title": "✅ Yes"}},
                    {"type": "reply", "reply": {"id": "language_no", "title": "❌ No"}},
                ]
            },
        },
    }
    async with httpx.AsyncClient() as http:
        resp = await http.post(settings.whatsapp_api_url, json=payload, headers=headers)
        resp.raise_for_status()


async def language_starting_message(sender_id: str) -> None:
    """Send the first lesson card (word index 0) with an intro message."""
    words = _get_words()
    if not words:
        from app.utils.whatsapp_func import send_whatsapp_message
        await send_whatsapp_message(
            sender_id,
            "Sorry, the language lesson content is being updated. Please try again shortly.",
        )
        return
    card = _format_lesson_card(words[0], 0, len(words))
    intro = (
        "Hi! Ready for your first language lesson of the day? "
        "Or feel free to ask us about any word or phrase you're curious about – "
        "We're happy to help you with that too! 😊\n\n"
        "Today's word/phrase is:\n\n"
        + card
        + "\n\nWould you like to learn more?"
    )
    await _send_lesson_with_buttons(sender_id, intro)


async def language_yes_message(sender_id: str, word_index: int = 1) -> None:
    """Send the lesson card at the given word_index (wraps around at end)."""
    words = _get_words()
    if not words:
        from app.utils.whatsapp_func import send_whatsapp_message
        await send_whatsapp_message(sender_id, "Sorry, lesson content unavailable. Try again shortly.")
        return
    idx = word_index % len(words)
    card = _format_lesson_card(words[idx], idx, len(words))
    body = "Here's your next word/phrase:\n\n" + card + "\n\nWould you like to learn more?"
    await _send_lesson_with_buttons(sender_id, body)


async def language_no_message(sender_id: str) -> None:
    """Send the 'What next?' options after user taps No."""
    headers = {
        "Authorization": f"Bearer {settings.access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": sender_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "What would you like to do next?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "language_phrase", "title": "💬 Ask Phrases"}},
                    {"type": "reply", "reply": {"id": "back_to_menu", "title": "🔙 Back to Menu"}},
                ]
            },
        },
    }
    async with httpx.AsyncClient() as http:
        resp = await http.post(settings.whatsapp_api_url, json=payload, headers=headers)
        resp.raise_for_status()


async def language_lesson_response(query: str, user_id: str) -> str:
    """
    Freestyle mode: try sheet lookup first, then AI fallback.
    Searches for matching English words in the lesson sheet before hitting OpenAI.
    """
    words = _get_words()

    # Sheet lookup: check if any English word in the lesson appears in the query
    if words:
        query_lower = query.lower()
        for i, word_data in enumerate(words):
            english = str(word_data.get("English", "")).lower().strip()
            if english and english in query_lower:
                card = _format_lesson_card(word_data, i, len(words))
                return f"Here's what I found in the lesson sheet:\n\n{card}"

    # AI fallback
    chat_history = get_conversation_history(user_id)
    conversation = trim_history(chat_history + [{"role": "user", "content": query}])

    prompt = (
        "You are a friendly Balinese and Indonesian language tutor for tourists visiting Bali.\n"
        "For each phrase or question:\n"
        "- Provide the phrase in both Balinese and Indonesian (if different).\n"
        "- Include a simple phonetic pronunciation for both.\n"
        "- Give a brief explanation of when/how to use it.\n"
        "- Keep a warm, helpful, culturally respectful tone.\n"
        "Do NOT use Markdown symbols (*, #, -, etc.) — plain text only for WhatsApp.\n"
        "Be concise."
    )

    try:
        completion = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt},
                *[{"role": m["role"], "content": m["content"]} for m in conversation[-6:]],
                {"role": "user", "content": query},
            ],
            max_tokens=350,
            temperature=0.4,
        )
        response = completion.choices[0].message.content
        save_message(user_id, "user", query)
        save_message(user_id, "assistant", response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")
