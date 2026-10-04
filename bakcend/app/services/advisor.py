from typing import List, Dict, Tuple
from app.schemas.advisory import AllocationItem, ProjectionMonth, AdvisoryResponse
from app.schemas.risk import RiskFormInput
from app.core.gemini_client import llm
from app.core.supabase_client import supabase
from app.services.embeddings import generate_embedding_with_retry

# Base Allocation Templates (Percentage Allocation)
ALLOCATION_TEMPLATES = {
    "Conservative": {
        "Fixed Deposits (FD)": 50.0,
        "Debt Mutual Funds": 30.0,
        "Equity SIPs": 15.0,
        "Gold": 5.0,
        "Crypto": 0.0
    },
    "Moderate": {
        "Fixed Deposits (FD)": 20.0,
        "Equity SIPs": 50.0,
        "Debt Mutual Funds": 15.0,
        "Gold": 10.0,
        "Crypto": 5.0
    },
    "Aggressive": {
        "Fixed Deposits (FD)": 10.0,
        "Equity SIPs": 65.0,
        "Debt Mutual Funds": 10.0,
        "Gold": 10.0,
        "Crypto": 5.0 # Max capped at 5%
    }
}

# Annual Return Scenarios (Min, Expected, Max %)
ANNUAL_RETURNS = {
    "Fixed Deposits (FD)": (0.06, 0.07, 0.075),
    "Debt Mutual Funds": (0.065, 0.08, 0.09),
    "Equity SIPs": (0.08, 0.12, 0.16),
    "Gold": (0.05, 0.09, 0.12),
    "Crypto": (-0.30, 0.15, 0.50)
}

class InvestmentAdvisorService:

    def calculate_allocation(self, risk_category: str, investable_amount: float) -> List[AllocationItem]:
        template = ALLOCATION_TEMPLATES.get(risk_category, ALLOCATION_TEMPLATES["Moderate"]).copy()
        
        allocations = []
        for instrument, pct in template.items():
            if pct > 0:
                m_amount = round((pct / 100.0) * investable_amount, 2)
                allocations.append(AllocationItem(
                    instrument=instrument,
                    percentage=pct,
                    monthly_amount=m_amount
                ))
        return allocations

    def calculate_12_month_projections(self, allocations: List[AllocationItem]) -> List[ProjectionMonth]:
        projections = []
        
        # Monthly compounding SIP growth model over 12 months
        for month in range(1, 13):
            cons_total = 0.0
            exp_total = 0.0
            opt_total = 0.0

            for item in allocations:
                P = item.monthly_amount
                if P <= 0:
                    continue
                
                min_r, exp_r, max_r = ANNUAL_RETURNS.get(item.instrument, (0.06, 0.08, 0.10))
                
                # Monthly compounding formula for regular monthly investments: FV = P * (((1 + r)^n - 1) / r) * (1 + r)
                r_cons, r_exp, r_opt = min_r / 12.0, exp_r / 12.0, max_r / 12.0

                cons_total += P * (((1 + r_cons)**month - 1) / r_cons) * (1 + r_cons) if r_cons != 0 else P * month
                exp_total += P * (((1 + r_exp)**month - 1) / r_exp) * (1 + r_exp) if r_exp != 0 else P * month
                opt_total += P * (((1 + r_opt)**month - 1) / r_opt) * (1 + r_opt) if r_opt != 0 else P * month

            projections.append(ProjectionMonth(
                month=month,
                conservative=round(cons_total, 2),
                expected=round(exp_total, 2),
                optimistic=round(opt_total, 2)
            ))
            
        return projections

    def retrieve_knowledge_context(self, query: str) -> str:
        """Fetch RAG context from knowledge_chunks if available."""
        try:
            emb = generate_embedding_with_retry(query)
            res = supabase.rpc("match_knowledge", {
                "query_embedding": emb,
                "match_threshold": 0.2,
                "match_count": 3
            }).execute()
            if res.data:
                return "\n".join([f"- {item['title']}: {item['content']}" for item in res.data])
        except Exception as e:
            print(f"Error querying knowledge chunks: {e}")
        return "Standard asset allocation rules apply based on risk tolerance and liquidity needs."

    def generate_explanation(self, risk_category: str, allocations: List[AllocationItem], investable_amount: float) -> str:
        alloc_summary = ", ".join([f"{item.percentage}% in {item.instrument}" for item in allocations])
        rag_context = self.retrieve_knowledge_context(f"Investment advice for {risk_category} risk profile")

        prompt = f"""You are a certified financial planner at FINMATE.
Explain the following monthly investment allocation to a user in plain, reassuring language:

User Profile: {risk_category} Risk
Investable Monthly Surplus: ₹{investable_amount}
Recommended Allocation: {alloc_summary}

Reference Financial Knowledge Context:
{rag_context}

Provide a concise 3-paragraph summary:
1. Why this specific asset breakdown fits their {risk_category} risk profile.
2. How the blend balances capital safety, guaranteed returns (FDs/Debt), and growth potential (Equity/SIPs).
3. Important risk reminder about market volatility.

Keep it simple, friendly, and non-jargon heavy.
"""
        try:
            res = llm.invoke(prompt)
            return res.content.strip()
        except Exception as e:
            return f"This allocation is tailored to your {risk_category} risk profile, balancing safe fixed-income assets with growth equity instruments."

advisor_service = InvestmentAdvisorService()