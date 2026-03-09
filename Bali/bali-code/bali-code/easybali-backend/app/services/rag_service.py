import logging
import pandas as pd
from typing import List, Optional, Dict, Any
from app.services.pinconeservice import get_index
from app.services.openai_client import client
from app.settings.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    @staticmethod
    async def get_rag_context(query: str, chat_type: str = "general", villa_code: str = "WEB_VILLA_01") -> str:
        """
        Unified RAG retrieval logic for both Web and WhatsApp.
        Intelligently selects the best Pinecone index based on query and chat_type.
        """
        try:
            # 1. Determine index search strategy
            indexes_to_search = []
            
            # Context-based index selection
            if chat_type == "things-to-do-in-bali" or any(kw in query.lower() for kw in ["visit", "see", "explore", "activity", "tour", "adventure"]):
                indexes_to_search.append(("things-to-do-in-bali", None))
            
            if chat_type == "local-cuisine" or any(kw in query.lower() for kw in ["food", "restaurant", "eat", "dining", "cuisine", "cafe"]):
                indexes_to_search.append(("local-cuisine", None))
            
            # Always check villa-faqs as it contains critical house rules and localized info
            # Filtered by villa_code for privacy and accuracy
            indexes_to_search.append(("villa-faqs", {"villa_code": villa_code}))

            # De-duplicate while preserving order (some might have matched multiple keywords)
            seen = set()
            unique_indexes = []
            for idx, filt in indexes_to_search:
                if idx not in seen:
                    unique_indexes.append((idx, filt))
                    seen.add(idx)

            # Generate embedding once
            embed_resp = await client.embeddings.create(input=query, model="text-embedding-ada-002")
            query_vector = embed_resp.data[0].embedding

            all_context_pieces = []
            
            for index_name, filter_dict in unique_indexes:
                index = get_index(index_name)
                if not index:
                    continue
                
                res = index.query(
                    vector=query_vector,
                    top_k=3,
                    include_metadata=True,
                    filter=filter_dict
                )
                
                matches = res.get("matches", [])
                for m in matches:
                    score = m.get("score", 0)
                    text = m.get("metadata", {}).get("text", "").strip()
                    if text and score > 0.70: # Standard 70% threshold for RAG reliability
                        # Prefix with source for AI clarity
                        source_label = index_name.replace("-", " ").title()
                        all_context_pieces.append(f"[{source_label}]: {text}")

            if not all_context_pieces:
                logger.info(f"RAG MISS for query: '{query[:50]}...' across {seen}")
                return ""

            final_context = "\n\n".join(all_context_pieces)
            logger.info(f"RAG HIT: Found {len(all_context_pieces)} pieces for query: '{query[:50]}...'")
            return final_context[:8000] # Token safety cap

        except Exception as e:
            logger.error(f"Unified RAG Service Error: {e}")
            return ""

rag_service = RAGService()
