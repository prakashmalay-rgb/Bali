# Easy Bali - RAG Pipeline Architecture

## Overview

The Retrieval-Augmented Generation (RAG) system inside Easy Bali provides specialized contextual knowledge (e.g. Activity recommendations, Local Cuisine guidance, and Villa FAQs) to the conversational AI models. Rather than solely relying on generalized intelligence, the system retrieves specific knowledge vectors and feeds them directly into the OpenAI token window seamlessly prior to generating responses.

## RAG Flow execution

- **Query Vectorization:** A user’s query (via WhatsApp or Web GUI) is routed to `ai_prompt.py`. The text string is immediately run through OpenAI's `text-embedding-ada-002` to extract a 1536-dimension float vector.
- **Index Identification:** Depending on the `chat_type` flag passed to the `generate_response()` orchestrator, the logic assigns the correct Pinecone index namespace:
  - `things-to-do-in-bali` -> `things-to-do-in-bali` index
  - `local-cuisine` -> `local-cuisine` index
  - Default -> `villa-faqs` index
- **Semantic Search:** The query vector is cross-referenced against the requested vector space inside Pinecone via Cosine Similarity (`get_rag_context()`).
- **Confidence Cutoff:** Only matches achieving a similarity score of strictly > `0.75` are returned. Lower-quality vectors are deemed irrelevant and scrubbed to prevent hallucination.
- **Context Injection:** Aggregated context strings are natively injected into the prompt’s `EXTERNAL KNOWLEDGE (RAG VILLA FAQs)` directive.

## LLM Fallback Reasoning & Monitoring

To prevent brittle behavior explicitly stated in system requirements:

- If zero matches exceed the `0.75` RAG threshold, the system immediately shifts into **LLM Fallback Mode**.
- The prompt includes a dynamic override clause directing the model to generate the most logical answer derived from core GPT weights *without* complaining about lacking context, simulating a seamless human response regardless of database depth.
- **Logging Pipeline:** Each retrieval execution emits a log metric determining whether the pipeline triggered a `RAG Retrieval SUCCESS` (mapping X vectors) or a `RAG Retrieval MISS` (initiating the LLM fallback scenario). Over time, these log spikes identify where the business must enrich the Google Sheets context pool.

## Data Ingestion Method

A background container task `ingest_faqs.py` extracts tabular headers from the administrative Google Sheet ("Villa FAQs"). For every `[Villa Code, Villa Name, Question, Answer]` row, a stringified context object is hashed and converted into embedding arrays before chunking into the Pinecone Serverless environment synchronously.
