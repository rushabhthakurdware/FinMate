from pydantic import BaseModel, Field
from typing import List, Optional

class KnowledgeChunkResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str

class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User question about financial concepts")

class SourceDocument(BaseModel):
    title: str
    category: str
    similarity: float

class ChatQueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]