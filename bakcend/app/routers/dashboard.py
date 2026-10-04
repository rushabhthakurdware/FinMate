from fastapi import APIRouter, Header, HTTPException
from typing import Optional
import pandas as pd
from app.core.supabase_client import supabase
from app.schemas.dashboard import DashboardSummary, CategoryBreakdown, MonthlyTrend, TopMerchant, RecentTransaction
from app.routers.transactions import get_user_id_from_header

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(authorization: Optional[str] = Header(None)):
    user_id = get_user_id_from_header(authorization)
    
    # Query all user transactions ordered by date descending
    res = supabase.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    data = res.data or []
    
    if not data:
        return DashboardSummary(
            total_spend=0.0,
            total_transactions=0,
            potential_savings=0.0,
            avoidable_percentage=0.0,
            category_breakdown=[],
            monthly_trend=[],
            top_merchants=[],
            recent_transactions=[]
        )

    df = pd.DataFrame(data)
    df["amount"] = df["amount"].astype(float)
    df["parsed_date"] = pd.to_datetime(df["date"])

    total_spend = float(df["amount"].sum())
    total_transactions = len(df)

    # Avoidable Expenses calculation
    avoidable_df = df[df["is_avoidable"] == True]
    potential_savings = float(avoidable_df["amount"].sum())
    avoidable_pct = round((potential_savings / total_spend * 100), 2) if total_spend > 0 else 0.0

    # 1. Category Breakdown
    cat_grouped = df.groupby("category")["amount"].sum().reset_index()
    category_breakdown = [
        CategoryBreakdown(
            category=row["category"],
            amount=round(float(row["amount"]), 2),
            percentage=round(float(row["amount"]) / total_spend * 100, 2) if total_spend > 0 else 0.0
        )
        for _, row in cat_grouped.iterrows()
    ]
    category_breakdown.sort(key=lambda x: x.amount, reverse=True)

    # 2. Monthly Trend
    df["month_str"] = df["parsed_date"].dt.strftime("%Y-%m")
    trend_grouped = df.groupby("month_str")["amount"].sum().reset_index()
    monthly_trend = [
        MonthlyTrend(
            month=row["month_str"],
            amount=round(float(row["amount"]), 2)
        )
        for _, row in trend_grouped.iterrows()
    ]
    monthly_trend.sort(key=lambda x: x.month)

    # 3. Top Merchants
    merchant_grouped = df.groupby("description").agg(
        amount=("amount", "sum"),
        count=("amount", "count")
    ).reset_index().sort_values(by="amount", ascending=False).head(5)

    top_merchants = [
        TopMerchant(
            merchant=row["description"],
            amount=round(float(row["amount"]), 2),
            count=int(row["count"])
        )
        for _, row in merchant_grouped.iterrows()
    ]

    # 4. Recent Transactions (Top 10) - SAFELY CAST DATE TO STRING
    recent_transactions = [
        RecentTransaction(
            id=str(row["id"]),
            date=str(row["date"]), # FIXED: Simple string cast avoids datetime errors
            description=row["description"],
            amount=round(float(row["amount"]), 2),
            category=row["category"],
            is_avoidable=bool(row.get("is_avoidable", False))
        )
        for row in data[:10]
    ]

    return DashboardSummary(
        total_spend=round(total_spend, 2),
        total_transactions=total_transactions,
        potential_savings=round(potential_savings, 2),
        avoidable_percentage=avoidable_pct,
        category_breakdown=category_breakdown,
        monthly_trend=monthly_trend,
        top_merchants=top_merchants,
        recent_transactions=recent_transactions
    )