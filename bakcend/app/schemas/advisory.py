from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class AllocationItem(BaseModel):
    instrument: str # e.g., "Fixed Deposit (FD)", "Mutual Funds / SIP", "Gold", "Crypto"
    percentage: float
    monthly_amount: float

class ProjectionMonth(BaseModel):
    month: int # 1 to 12
    conservative: float
    expected: float
    optimistic: float

class AdvisoryResponse(BaseModel):
    risk_category: str
    investable_monthly_amount: float
    allocation: List[AllocationItem]
    projections: List[ProjectionMonth]
    explanation: str
    crypto_warning: Optional[str] = None
    disclaimer: str