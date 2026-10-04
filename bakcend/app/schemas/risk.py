from pydantic import BaseModel, Field
from typing import List, Optional

class RiskFormInput(BaseModel):
    age: int = Field(..., ge=18, le=100, description="User age in years")
    monthly_income: float = Field(..., gt=0, description="Monthly net income")
    emi_amount: float = Field(0.0, ge=0, description="Total monthly EMI payments")
    dependents: int = Field(0, ge=0, description="Number of financial dependents")
    savings: float = Field(0.0, ge=0, description="Total current savings/emergency fund")
    horizon_years: int = Field(..., ge=1, le=40, description="Target investment horizon in years")

class RiskAssessmentResponse(BaseModel):
    risk_score: float # Score between 0 and 100
    category: str # Conservative, Moderate, Aggressive
    emi_ratio: float
    savings_months: float
    factors: List[str]