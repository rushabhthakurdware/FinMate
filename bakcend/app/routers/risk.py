from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from app.schemas.risk import RiskFormInput, RiskAssessmentResponse
from app.services.risk_model import risk_service
from app.core.supabase_client import supabase
from app.routers.transactions import get_user_id_from_header

router = APIRouter(prefix="/risk", tags=["Risk Profiling"])

@router.post("/evaluate", response_model=RiskAssessmentResponse)
def evaluate_and_save_risk(
    form_data: RiskFormInput,
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id_from_header(authorization)
    risk_score, category, factors = risk_service.evaluate_risk(form_data)
    
    emi_ratio = round(form_data.emi_amount / form_data.monthly_income, 4) if form_data.monthly_income > 0 else 0.0
    savings_months = round(form_data.savings / form_data.monthly_income, 2) if form_data.monthly_income > 0 else 0.0

    # Save or update risk profile in Supabase
    db_payload = {
        "user_id": user_id,
        "age": form_data.age,
        "monthly_income": form_data.monthly_income,
        "emi_amount": form_data.emi_amount,
        "dependents": form_data.dependents,
        "savings": form_data.savings,
        "horizon_years": form_data.horizon_years,
        "risk_score": risk_score,
        "category": category
    }

    try:
        supabase.table("risk_profiles").upsert(db_payload, on_conflict="user_id").execute()
    except Exception as e:
        print(f"Error saving risk profile: {e}")

    return RiskAssessmentResponse(
        risk_score=risk_score,
        category=category,
        emi_ratio=emi_ratio,
        savings_months=savings_months,
        factors=factors
    )

@router.get("/my-profile")
def get_user_risk_profile(authorization: Optional[str] = Header(None)):
    user_id = get_user_id_from_header(authorization)
    res = supabase.table("risk_profiles").select("*").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Risk profile not found")
    return res.data[0]