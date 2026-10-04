from pydantic import BaseModel
from typing import List, Dict

class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float

class MonthlyTrend(BaseModel):
    month: str # Format: "YYYY-MM"
    amount: float

class TopMerchant(BaseModel):
    merchant: str
    amount: float
    count: int

class RecentTransaction(BaseModel):
    id: str
    date: str
    description: str
    amount: float
    category: str
    is_avoidable: bool
    
class DashboardSummary(BaseModel):
    total_spend: float
    total_transactions: int
    potential_savings: float # Total from avoidable items
    avoidable_percentage: float
    category_breakdown: List[CategoryBreakdown]
    monthly_trend: List[MonthlyTrend]
    top_merchants: List[TopMerchant]
    recent_transactions: List[RecentTransaction] # New field