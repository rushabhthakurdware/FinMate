from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class TransactionCreate(BaseModel):
    date: date
    description: str
    amount: float
    category: Optional[str] = None
    is_avoidable: Optional[bool] = False

class TransactionResponse(BaseModel):
    id: str
    date: date
    description: str
    amount: float
    category: str
    is_avoidable: bool
    source: str

class CategoryCorrection(BaseModel):
    transaction_id: str
    new_category: str
    is_avoidable: Optional[bool] = False

class CategorizationResult(BaseModel):
    category: str
    is_avoidable: bool
    confidence: float