from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from app.schemas.advisory import AdvisoryResponse
from app.schemas.risk import RiskFormInput
from app.services.advisor import advisor_service
from app.services.risk_model import risk_service
from app.core.supabase_client import supabase
from app.routers.transactions import get_user_id_from_header

router = APIRouter(prefix="/advisory", tags=["Investment Advisory"])

DISCLAIMER_TEXT = "DISCLAIMER: These projections are illustrative estimates based on historical asset parameters and do not constitute formal financial advice. Market investments are subject to risk."

@router.post("/recommend", response_model=AdvisoryResponse)
def get_investment_recommendation(
    form_data: RiskFormInput,
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id_from_header(authorization)
    
    # 1. Evaluate risk category
    _, category, _ = risk_service.evaluate_risk(form_data)
    
    # 2. Compute monthly surplus (Income - EMI)
    monthly_surplus = max(0.0, form_data.monthly_income - form_data.emi_amount)
    # Recommend allocating 40% of net surplus towards investments (safety threshold)
    investable_monthly = round(monthly_surplus * 0.40, 2)
    
    if investable_monthly <= 0:
        investable_monthly = 1000.0 # Default minimum fallback for calculation

    # 3. Generate Allocation & Projections
    allocations = advisor_service.calculate_allocation(category, investable_monthly)
    projections = advisor_service.calculate_12_month_projections(allocations)
    explanation = advisor_service.generate_explanation(category, allocations, investable_monthly)

    crypto_warning = None
    if category == "Aggressive":
        crypto_warning = "NOTICE: Crypto is capped at 5% due to high price volatility and lack of regulatory insurance. Never invest funds required for short-term needs."

    # 4. Store in advice_history table
    try:
        supabase.table("advice_history").insert({
            "user_id": user_id,
            "allocation": [item.model_dump() for item in allocations],
            "projections": [p.model_dump() for p in projections],
            "explanation": explanation
        }).execute()
    except Exception as e:
        print(f"Error persisting advice history: {e}")

    return AdvisoryResponse(
        risk_category=category,
        investable_monthly_amount=investable_monthly,
        allocation=allocations,
        projections=projections,
        explanation=explanation,
        crypto_warning=crypto_warning,
        disclaimer=DISCLAIMER_TEXT
    )