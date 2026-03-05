# 🔒 Regression Prevention Guide — EASYBali Payment Links & Chat

> Last updated: 2026-03

---

## 🚨 Root Causes of Past Regressions

### 1. Frontend API URL Misconfiguration (PRIMARY)

- **What broke:** `apiClient.js` had a fallback of `localhost:8001` (wrong port).
  All payment link requests silently routed to the wrong URL.
- **Fix applied:**
  - Created `bali-frontend/.env` → `VITE_API_URL=http://localhost:8000`
  - Created `bali-frontend/.env.development` → same
  - Fixed fallback in `apiClient.js` from `8001` → `8000`
  - Added a loud `console.error` guard-rail when `VITE_API_URL` is missing

### 2. WhatsApp NFM Reply — Silent Booking Drop

- **What broke:** The flow handler required ALL 5 fields (`flow_token`, `selected_service`, `selected_date`, `person_selection`, `time_selection`). If any optional field was missing the payment link was never created and the user got zero feedback.
- **Fix applied:**
  - Changed the gate to only require the 3 critical fields
  - `person_selection` defaults to `"1"`, `time_selection` defaults to `"Flexible"`
  - Added explicit error message when required fields are missing

### 3. WhatsApp AI List Message — Wrong Message Type

- **What broke:** `send_ai_whatsapp_list_message` used `"type": "cta_url"` which does NOT support `sections`/`rows`. WhatsApp API rejected silently.
- **Fix applied:** Switched to `"type": "list"`. Image is now sent separately first (with caption) if available.

### 4. Missing `maintenance-issue` Chat Type Handler

- **What broke:** Clicking "Report Issue" in the website chat had no dedicated AI path — it fell into the general service-booking interceptor.
- **Fix applied:** Added `"maintenance-issue"` to `PERSONAS` dict and added isolated handler block in `process_query()`.

### 5. Voice Translator — Incomplete Transcript Auto-Send

- **What broke:** `useVoiceToText.js` only accumulated per-event chunks. The running `fullTranscript` wasn't tracked, so if speech was chunked into multiple `onresult` events the auto-send would only include the last chunk.
- **Fix applied:** Added `fullTranscriptRef` to accumulate ALL finalised chunks. Auto-send always has the full spoken message.

---

## 🛡 Anti-Regression Checklist (Run Before Every Deploy)

| Check | Command / How |
|-------|---------------|
| Frontend `.env` exists | `ls bali-frontend/.env` — must show `VITE_API_URL=http://localhost:8000` |
| Backend starts without error | `uvicorn main:app --port 8000` — check no import errors |
| Payment link (website) | Chat → Order Services → book a service → confirm → payment URL appears |
| Payment link (WhatsApp) | Complete the WhatsApp flow → receive "Pay Now" CTA button |
| Voice translator | Click mic → speak → text types live → message auto-sends when mouth stops |
| Maintenance Issue menu | Click "Report Issue" in website chat → bot responds with maintenance prompt |
| Currency Converter | Type "Convert 100 USD to IDR" → gets a number response |
| Plan My Trip | Type "Plan my 3 days in Bali" → gets itinerary |

---

## ⚙️ How `VITE_API_URL` Works

```
bali-frontend/.env          ← loaded always (dev + prod build)
bali-frontend/.env.development  ← loaded only in dev (npm run dev)
bali-frontend/.env.production   ← loaded only in prod builds
```

For Render / production deployment, set `VITE_API_URL=https://bali-v92r.onrender.com`
as an environment variable in the Render dashboard — **never hard-code it in source**.

---

## 🏗 Architecture Reminder

```
Website Chat (chat.jsx)
  └─► apiClient.js  ──► VITE_API_URL ──► FastAPI backend (port 8000)
                                              └─► payment_service.py
                                              └─► create_xendit_payment_with_distribution()
                                              └─► Xendit API → payment_url

WhatsApp
  └─► Meta Webhook ──► whatsapp_routes.py
                           └─► process_message() in whatsapp_func.py
                               └─► nfm_reply handler
                                   └─► create_xendit_payment_with_distribution()
                                   └─► send_interactive_message() → CTA "Pay Now"
```
