import time
import logging
from typing import List
from app.core.gemini_client import embeddings_model

logger = logging.getLogger(__name__)

def generate_embedding_with_retry(text: str, max_retries: int = 3) -> List[float]:
    """Generates a 768-dim embedding with exponential backoff for Gemini free tier rate limits."""
    for attempt in range(max_retries):
        try:
            vector = embeddings_model.embed_query(text)
            return vector
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to generate embedding for text '{text}': {e}")
                # Fallback to zero vector if LLM embedding fails
                return [0.0] * 768
            time.sleep(2 ** attempt)

def generate_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Batch processes texts into 768-dim vectors."""
    try:
        return embeddings_model.embed_documents(texts)
    except Exception as e:
        logger.warning(f"Batch embedding failed, falling back to sequential retry: {e}")
        return [generate_embedding_with_retry(text) for text in texts]