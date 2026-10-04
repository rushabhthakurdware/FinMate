import json
import os
import re
from typing import Tuple, List, Dict
from app.core.supabase_client import supabase
from app.core.gemini_client import llm
from app.services.embeddings import generate_embedding_with_retry

RULES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "rules.json")

def load_rules() -> Dict[str, List[str]]:
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return {}

AVOIDABLE_CATEGORIES = {"Food & Dining", "Shopping & Retail", "Entertainment & Subscriptions"}

class HybridCategorizer:
    def __init__(self):
        self.rules = load_rules()

    def categorize_by_rules(self, description: str) -> Tuple[str, bool]:
        """Step A: Keyword/Merchant matching."""
        desc_clean = description.lower()
        for category, keywords in self.rules.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', desc_clean):
                    is_avoidable = category in AVOIDABLE_CATEGORIES
                    return category, is_avoidable
        return "Uncategorized", False

    def retrieve_few_shot_examples(self, user_id: str, embedding: List[float], limit: int = 5) -> List[Dict]:
        """Step B: Retrieve top 5 similar transactions from pgvector."""
        try:
            res = supabase.rpc(
                "match_transactions",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.3,
                    "match_count": limit,
                    "p_user_id": user_id
                }
            ).execute()
            return res.data or []
        except Exception as e:
            print(f"Error fetching vector context: {e}")
            return []

    def categorize_with_llm(self, description: str, amount: float, few_shots: List[Dict]) -> Tuple[str, bool]:
        """Step C: Few-shot fallback via Gemini."""
        examples_str = ""
        if few_shots:
            examples_str = "\n".join([f"- Transaction: '{ex['description']}' -> Category: '{ex['category']}'" for ex in few_shots])
        
        prompt = f"""You are a financial transaction classification expert.
Categorize the following transaction into one of these standard categories:
[Food & Dining, Groceries, Transportation, Shopping & Retail, Entertainment & Subscriptions, Bills & Utilities, Healthcare, Investment, Income, Miscellaneous]

Context / Past similar user transactions:
{examples_str if examples_str else "No past examples found."}

Target Transaction:
Description: "{description}"
Amount: {amount}

Respond strictly in valid JSON format with keys "category" and "is_avoidable" (boolean).
Example format:
{{"category": "Food & Dining", "is_avoidable": true}}
"""
        try:
            response = llm.invoke(prompt)
            cleaned_text = response.content.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:-3].strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:-3].strip()
            
            data = json.loads(cleaned_text)
            category = data.get("category", "Miscellaneous")
            is_avoidable = data.get("is_avoidable", category in AVOIDABLE_CATEGORIES)
            return category, is_avoidable
        except Exception as e:
            print(f"LLM Categorization failed: {e}")
            return "Miscellaneous", False

    def process_transaction(self, user_id: str, description: str, amount: float) -> Tuple[str, bool, List[float]]:
        # 1. Rules engine check
        category, is_avoidable = self.categorize_by_rules(description)
        embedding = generate_embedding_with_retry(description)
        
        if category != "Uncategorized":
            return category, is_avoidable, embedding
        
        # 2. Vector retrieval + Few-shot LLM fallback
        few_shots = self.retrieve_few_shot_examples(user_id, embedding)
        category, is_avoidable = self.categorize_with_llm(description, amount, few_shots)
        
        return category, is_avoidable, embedding

categorizer = HybridCategorizer()