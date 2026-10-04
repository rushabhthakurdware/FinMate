import json
import os
from typing import List, Dict, Tuple
from app.core.supabase_client import supabase
from app.core.gemini_client import llm
from app.services.embeddings import generate_embedding_with_retry

DOCS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_docs.json")

class RAGKnowledgeService:

    def seed_knowledge_chunks(self) -> int:
        """Seed pre-written knowledge docs into Supabase with vector embeddings."""
        if not os.path.exists(DOCS_FILE):
            return 0

        with open(DOCS_FILE, "r") as f:
            docs = json.load(f)

        records = []
        for doc in docs:
            # Check if chunk already exists by title
            existing = supabase.table("knowledge_chunks").select("id").eq("title", doc["title"]).execute()
            if existing.data:
                continue

            emb = generate_embedding_with_retry(f"{doc['title']}: {doc['content']}")
            records.append({
                "title": doc["title"],
                "category": doc["category"],
                "content": doc["content"],
                "embedding": emb
            })

        if records:
            supabase.table("knowledge_chunks").insert(records).execute()
            return len(records)
        return 0

    def query_rag_knowledge(self, question: str) -> Tuple[str, List[Dict]]:
        """Retrieve relevant knowledge chunks and generate a grounded LLM answer."""
        query_embedding = generate_embedding_with_retry(question)

        # Vector search in pgvector via RPC call
        try:
            res = supabase.rpc("match_knowledge", {
                "query_embedding": query_embedding,
                "match_threshold": 0.25,
                "match_count": 3
            }).execute()
            retrieved_chunks = res.data or []
        except Exception as e:
            print(f"Error executing match_knowledge: {e}")
            retrieved_chunks = []

        if not retrieved_chunks:
            context_text = "No relevant internal documentation found."
        else:
            context_text = "\n\n".join([f"Source ({chunk['title']}): {chunk['content']}" for chunk in retrieved_chunks])

        prompt = f"""You are "Ask FINMATE", an AI Financial Knowledge Assistant.
Answer the user's question accurately using ONLY the context provided below.
If the answer cannot be determined strictly from the context, state clearly that you do not have enough verified context in the knowledge base and provide a brief general guideline with a standard disclaimer.

User Question: "{question}"

Verified Knowledge Context:
{context_text}

Provide a concise, direct, helpful response in Markdown format.
"""
        try:
            response = llm.invoke(prompt)
            answer = response.content.strip()
        except Exception as e:
            answer = f"I'm sorry, I encountered an issue retrieving the answer: {str(e)}"

        sources = [
            {
                "title": chunk.get("title", "Financial Guide"),
                "category": chunk.get("category", "General"),
                "similarity": round(chunk.get("similarity", 0.0), 4)
            }
            for chunk in retrieved_chunks
        ]

        return answer, sources

rag_service = RAGKnowledgeService()