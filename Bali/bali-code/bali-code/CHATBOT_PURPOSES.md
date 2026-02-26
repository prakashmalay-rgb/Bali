# Chatbot Consolidation & Purpose Documentation

## Executive Summary

The EASY Bali platform features an array of AI Concierge assistants. Based on the stabilization and consolidation phase, we have structured the chatbot logic to ensure deterministic routing without logical overlap. Generic bots utilize centralized logic (`ai_prompt.py`), while highly-specialized RAG index bots run isolated logic endpoints.

## Directory of Assistants & Rules

### 1. General AI Concierge (`/general`)

- **Purpose**: Acts as the default catch-all property AI for guests in villas.
- **Data Boundary**: Operates as a premium concierge. Leverages internal data (Services sheet) and general knowledge to handle direct amenity requests.
- **Engine**: Centralized `generate_response()` via `ai_prompt.py`.

### 2. Local Guide (Cuisine) (`/local-cuisine`)

- **Purpose**: The absolute authority on food, warungs, and dining in Bali. Replaces generic "Recommendations".
- **Data Boundary**: **STRICT**. It will actively reject non-food queries (e.g., flight info, visas) via prompt-level enforcement. Integrates directly with the `local-cuisine` Pinecone RAG index.
- **Engine**: Isolated route (`local_cuisine.py`).

### 3. Event Calendar (`/event-calender`)

- **Purpose**: To provide up-to-date, culturally aware event scheduling.
- **Data Boundary**: Scopes entirely to the `event-calender` Pinecone RAG index.
- **Engine**: Isolated route (`event_calender.py`).

### 4. What To Do Today? (`/what-to-do`)

- **Purpose**: Highly curated, spontaneous activity planner.
- **Data Boundary**: Focuses on internal DB activities first.
- **Engine**: Centralized `generate_response()` via `ai_prompt.py`.

### 5. Plan My Trip! (`/plan-my-trip`)

- **Purpose**: A structured wizard designed to build multi-day itineraries systematically (Days -> Base -> Interests -> Budget).
- **Data Boundary**: Interactive step-by-step constraint.
- **Engine**: Centralized `generate_response()` via `ai_prompt.py`.

### 6. Currency Converter (`/currency-converter`)

- **Purpose**: Fast mathematical IDR conversion.
- **Data Boundary**: Enforced persona constraints.
- **Engine**: Centralized `generate_response()` via `ai_prompt.py`.

### 7. Voice Translator (`/voice-translator` or `language_lesson.py`)

- **Purpose**: Transcribes vocal requests and teaches Balinese/Indonesian terms. Employs Whisper API for audio-to-text.
- **Data Boundary**: Focuses solely on linguistic conversions and phrase teaching.
- **Engine**: Centralized routing via frontend Whisper transcription + `ai_prompt.py` backend language routing.

## Consolidation Conclusion

"Recommendations" has been strategically merged into the "Local Guide" architecture to prevent hallucination overlapping. Users seeking general activities trigger "What To Do Today". Users seeking dining trigger "Local Guide". This completely prevents logical conflicts.
