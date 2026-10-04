from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.knowledge import KnowledgeChunkResponse, ChatQueryRequest, ChatQueryResponse
from app.services.rag import rag_service
from app.core.supabase_client import supabase

router = APIRouter(prefix="/knowledge", tags=["Knowledge Center (RAG)"])

@router.post("/seed")
def seed_knowledge_base():
    """Seed static knowledge articles into pgvector storage."""
    count = rag_service.seed_knowledge_chunks()
    return {"message": f"Successfully seeded {count} knowledge chunks into pgvector."}

@router.get("/articles", response_model=List[KnowledgeChunkResponse])
def get_all_knowledge_articles():
    """Fetch all knowledge articles for static cards view."""
    res = supabase.table("knowledge_chunks").select("id, title, content, category").execute()
    return res.data or []

@router.post("/ask", response_model=ChatQueryResponse)
def ask_finmate_chatbot(request: ChatQueryRequest):
    """RAG Chatbot endpoint that answers questions grounded strictly in retrieved chunks."""
    answer, sources = rag_service.query_rag_knowledge(request.question)
    return ChatQueryResponse(
        answer=answer,
        sources=sources
    )