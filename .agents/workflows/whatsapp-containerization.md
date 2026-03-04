---
description: WhatsApp Module Containerization - No Regression Rule
---

# 🔒 CHAT MODULE — FULLY CONTAINERIZED (DO NOT MODIFY)

> **Locked on: 2026-03-04**
> **Last verified: 2026-03-04 @ 22:25 IST**
> **Status: ✅ PRODUCTION-PROVEN — PAYMENT LINK FLOW LIVE — ZERO TOLERANCE FOR REGRESSION**

This workflow enforces a **no-regression policy** across the entire Chat module — both the **WhatsApp bot** and the **Website chatbot** — spanning backend services, routes, utilities, data models, schemas, frontend components, hooks, and API layers.

---

## ❌ ABSOLUTE RULES — NEVER VIOLATE

1. **NO direct edits** to any file listed below — period.
2. **NO refactoring** — no renaming functions, classes, variables, columns, or env vars.
3. **NO dependency changes** — no adding/removing/upgrading packages that affect these files.
4. **NO schema changes** — Pydantic models, DB collections, and Google Sheets column names are frozen.
5. **BASE_URL must always be used** — never hardcode `onrender.com` or `localhost`.
6. **Google Sheets columns must never be assumed** — always guard with `if "ColName" in df.columns`.
7. **Price values from Google Sheets MUST be cleaned with `re.sub(r'[^\d]', '', str(price))`** before any int() conversion — sheets contain `\xa0` non-breaking spaces.
8. **Never make loopback HTTP calls** — use direct Python service calls (not `httpx` to `settings.BASE_URL`) for internal data fetching within the same process.

---

## ✅ WHAT IS PROVEN WORKING (DO NOT TOUCH)

The following end-to-end flow is **live and verified** on Render production:

1. Customer scans QR → WhatsApp bot greets and identifies villa
2. Customer selects menu → Services pulled from Google Sheets with real pricing
3. Customer selects service via WhatsApp Flow → Booking confirmation screen
4. On submit → Order created in MongoDB (order_number `EB*`)
5. Xendit invoice created → Interactive **Pay Now** button sent via WhatsApp CTA message
6. Payment link received by customer in WhatsApp ✅

---

## 🔒 PROTECTED FILES — BACKEND (Python/FastAPI)

### Core WhatsApp AI Pipeline

- `app/services/whatsapp_ai_prompt.py` — WhatsApp AI response generation (3-path: menu/decline/conversation)
- `app/services/ai_menu_generator.py` — Service intent detection, keyword matching, menu generation
- `app/services/whatsapp_queue.py` — Message queue processor
- `app/utils/whatsapp_func.py` — All WhatsApp message handling, `process_message`, send functions
  - **KEY**: `fetch_menu_data`, `fetch_submenu_data`, `fetch_service_items`, `fetch_menu_design`, `fetch_whatsapp_numbers` all use **direct Python calls** (NOT HTTP)
  - **KEY**: `nfm_reply` handler strips `ai_service_N_` prefix from service IDs before price lookup
  - **KEY**: Price is cleaned with `re.sub(r'[^\d]', '', price)` before `int()` conversion
  - **KEY**: Date parsed with `dateutil.parser.parse()` — handles all ISO date formats

### Core Website Chatbot AI Pipeline

- `app/services/ai_prompt.py` — `ConciergeAI` class with isolated chat-type routing (currency, trip, general, etc.)
- `app/services/openai_client.py` — OpenAI client singleton
- `app/services/pinconeservice.py` — Pinecone vector DB connection (RAG retrieval)

### Routes

- `app/routes/whatsapp_routes.py` — WhatsApp webhook endpoints, flow handlers, crypto encryption
- `app/routes/chatbot_routes.py` — Website chatbot API endpoints (`/chatbot/*`)
- `app/routes/websockett.py` — WebSocket session management for live bookings
- `app/routes/service_inquiry.py` — Service inquiry creation, provider notification, payment pipeline

### Data & Models

- `app/models/chatbot_models.py` — `ChatRequest`, `MenuRequest`, `ServiceRequest` Pydantic models
- `app/models/order_summary.py` — Order data models
- `app/schemas/ai_response.py` — `ChatbotResponse`, `ChatbotQuery` schemas

### Services & Utilities

- `app/services/menu_services.py` — Google Sheets cache, data refresh, category/service lookups
  - **KEY**: `get_service_base_price()` strips `\xa0` non-breaking spaces from returned price
  - **KEY**: Fuzzy match fallback — normalizes `[^a-z0-9]` for resilient service name matching
  - **KEY**: `get_main_menu_design` is imported from `menu_services` (NOT `google_sheets_service`)
- `app/services/google_sheets_service.py` — Service data aggregation from cached DataFrames
- `app/services/google_sheets.py` — Raw Google Sheets workbook access
- `app/services/flow_encrytion.py` — WhatsApp Flow encryption/decryption
- `app/services/websocket_managerr.py` — WebSocket `ConnectionManager` singleton
- `app/services/order_summary.py` — Order state management, order ID generation
- `app/services/payment_service.py` — Xendit payment creation with split distribution (direct calls only)
- `app/utils/chat_memory.py` — In-memory conversation history
- `app/utils/data_processing.py` — DataFrame cleaning utility (`clean_dataframe`)
- `app/utils/navigation_rules.py` — Service navigation rules for AI context

### Configuration & Registration

- `app/settings/config.py` — Environment settings (Pydantic `Settings` class)
- `main.py` — Router registration, CORS, startup/shutdown events

---

## 🔒 PROTECTED FILES — FRONTEND (React)

### Chat Components

- `src/components/chatbot/chat.jsx` — Main chat UI component (WebSocket + API messaging, booking flow, service selection)
- `src/components/chatbot/chatbox.jsx` — Chat container wrapper

### Chat Logic & API

- `src/hooks/useChatLogic.js` — Chat state management hook (menu routing, API calls, WebSocket lifecycle)
- `src/api/chatApi.jsx` — Chat API client (sendMessage, createPayment, uploadPassport, uploadAudio, history)
- `src/api/apiClient.js` — Base API client (BASE_URL, error handling, request wrapper)

### Supporting Components

- `src/components/services/PassportSubmission.jsx` — Passport upload flow
- `src/components/services/IssueReporting.jsx` — Issue reporting UI
- `src/hooks/useVoiceToText.js` — Voice-to-text hook for voice translator

### Context & Styling

- `src/context/LanguageContext.jsx` — Language context provider (EN/ID switching)
- `src/style/pages/_chat.scss` — Chat styling

### Assets

- `src/assets/icons/chat-logo.png` — Chat logo icon
- `src/assets/images/ai-chat-icon.png` — AI chat icon

---

## ✅ WHEN CHANGES ARE ALLOWED

Changes to containerized files are **ONLY** permitted when:

1. **USER explicitly requests a fix** to a specific chat feature (e.g., "fix the currency converter chat")
2. The fix must be **surgical** — minimum diff, no refactoring
3. **ALL existing function signatures must be preserved**
4. **ALL existing API contracts must be preserved** (endpoints, request/response shapes)
5. The change must be **backward compatible** — no breaking existing behavior

---

## 🆕 HOW TO ADD NEW FEATURES

New features **MUST be added as NEW files** — never by editing containerized files:

1. Create new routes in `app/routes/new_feature_routes.py`
2. Create new services in `app/services/new_feature_service.py`
3. Register via `try/except` in `main.py` (so a failure doesn't crash existing routes)
4. Frontend: create new components in `src/components/new_feature/`
5. New hooks go in `src/hooks/useNewFeature.js`

---

## 🔍 VERIFICATION CHECKLIST (Before Any Deploy)

// turbo-all

1. Run `python -c "from app.settings.config import settings; print(settings.BASE_URL)"` — must print correct URL
2. Run `python -c "from main import app; print([r.path for r in app.routes])"` — must list all routes including `/chatbot/*`
3. Confirm `.env` has all required keys from `config.py`
4. Confirm `requirements.txt` includes `python-dateutil` (for robust date parsing)
5. Confirm no hardcoded `onrender.com` URLs: `grep -r "onrender.com" app/ --include="*.py"`
6. Confirm no loopback HTTP calls in `whatsapp_func.py` fetch functions — must use direct Python service imports
7. Confirm `get_service_base_price` in `menu_services.py` strips non-digit chars before returning

---

## 🐛 KNOWN PITFALLS (DO NOT RE-INTRODUCE)

| Bug | Root Cause | Fix Applied |
|-----|-----------|-------------|
| "Invalid date format" | WhatsApp sends ISO8601 dates, `strptime('%Y-%m-%d')` rejected them | Use `dateutil.parser.parse()` |
| "IDR 0" price / Xendit rejected | `ai_service_N_Name` ID sent; exact match failed → price=0 | Strip `ai_service_N_` prefix + fuzzy match |
| "Issue generating payment link" | `int(price)` crashed on `\xa0` non-breaking space from Google Sheets | `re.sub(r'[^\d]', '', price)` before int() |
| Server startup crash on Render | `get_main_menu_design` imported from wrong module (`google_sheets_service`) | Move import to `menu_services` |
| Menu options silent failure | `fetch_*` functions used loopback HTTP calls that Render's routing blocks | Convert to direct Python service calls |
| `KeyError: 'Menu Location'` | Google Sheets cache partly loaded; column missing | All accesses use `.get()` with defaults |
