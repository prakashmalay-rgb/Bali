# RAG Architecture: EASYBali AI Concierge

## Overview

EASYBali uses a RAG (Retrieval-Augmented Generation) pipeline to provide accurate, villa-specific information to guests. This ensures that the AI doesn't just hallucinate answers but relies on verified data from Google Sheets.

## Data High-Speed Rail (Ingestion Pipeline)

1. **Source**: Multiple worksheets in the master Google Sheet:
    - **Villa FAQs**: General house rules, WiFi, pool instructions.
    - **Local Guide/Cuisine**: Recommendations for local dining and culture.
    - **Event Calendar**: Upcoming festivities and things to do.
2. **Processing**: The `ingest_faqs.py` script:
    - Reads data from Google Sheets.
    - Sanitizes and formats text into chunks.
    - Generates 1536-dimensional embeddings using OpenAI's `text-embedding-ada-002`.
3. **Storage**: Vectors are upserted into three separate Pinecone indexes:
    - `villa-faqs`
    - `local-cuisine`
    - `things-to-do-in-bali`

## Retrieval Strategy

When a user asks a question, the `ConciergeAI` module:

1. Detects the `chat_type` (persona).
2. Routes the query to the corresponding Pinecone index.
3. Performs a similarity search (Cosine Similarity).
4. Filters results based on a **75% confidence threshold**.
5. If matches are found, they are injected into the system prompt as `EXTERNAL KNOWLEDGE`.

## Fallback Mechanism

- If RAG retrieval fails or returns low-confidence matches:
  - The system falls back to **Internal Sheets Context** (direct row lookup).
  - If that also fails, it uses **LLM Reasoning** based on high-end hospitality standards.
- The AI is instructed to never state "I don't have context" but to synthesize a logical, helpful response.

## Personas & Specialization

- **Activity Expert**: Prioritizes `things-to-do-in-bali` index.
- **Language Mentor**: Uses cultural nuances and a specific teaching persona.
- **Security Assistant**: Focuses on passport compliance and house safety.
