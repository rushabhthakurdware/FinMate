from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Header
from typing import List, Optional
import pandas as pd
from io import BytesIO
import jwt
import pdfplumber
import re
from datetime import datetime

from app.core.config import settings
from app.core.supabase_client import supabase
from app.schemas.transaction import TransactionCreate, TransactionResponse, CategoryCorrection
from app.services.categorizer import categorizer
from app.services.embeddings import generate_embedding_with_retry

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract user_id from Supabase JWT or provide a test fallback user."""
    if not authorization:
        return "00000000-0000-0000-0000-000000000000"  # Development Fallback UUID
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
        return payload.get("sub", "00000000-0000-0000-0000-000000000000")
    except Exception:
        return "00000000-0000-0000-0000-000000000000"


def extract_transactions_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """Extracts date, description, and amount from unstructured bank PDF statements."""
    parsed_rows = []
    
    # Enhanced regex to capture dates (DD/MM/YYYY or YYYY-MM-DD), description, and amounts with optional currency symbols or Cr/Dr
    row_pattern = re.compile(
        r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\s+(.*?)\s+(?:(?:Rs\.?|₹)?\s*)([\d,]+\.\d{2})\s*(?:Cr|Dr)?',
        re.IGNORECASE
    )

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for line in text.split('\n'):
                match = row_pattern.search(line)
                if match:
                    raw_date, desc, amount_str = match.groups()
                    clean_amount = float(amount_str.replace(',', ''))
                    if clean_amount > 0:
                        parsed_rows.append({
                            "date": raw_date.strip(),
                            "description": desc.strip(),
                            "amount": abs(clean_amount)
                        })
                    
    return parsed_rows


@router.post("/add")
def add_single_transaction(
    tx: TransactionCreate,
    authorization: Optional[str] = Header(None)
):
    """Allows adding a quick single expense directly from the Dashboard UI."""
    user_id = get_user_id_from_header(authorization)
    category, is_avoidable, embedding = categorizer.process_transaction(user_id, tx.description, tx.amount)

    record = {
        "user_id": user_id,
        "date": str(tx.date),
        "description": tx.description,
        "amount": tx.amount,
        "category": category,
        "is_avoidable": is_avoidable,
        "source": "manual",
        "embedding": embedding
    }

    res = supabase.table("transactions").insert([record]).execute()
    return {"message": "Transaction added successfully", "data": res.data}


@router.post("/upload-statement")
async def upload_statement(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """Processes bank statements in either CSV or PDF format."""
    user_id = get_user_id_from_header(authorization)
    filename = file.filename.lower()
    contents = await file.read()
    raw_records = []

    # 1. Process CSV Files
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(BytesIO(contents))
            df.columns = df.columns.str.lower().str.strip()
            date_col = next((c for c in df.columns if "date" in c), None)
            desc_col = next((c for c in df.columns if "desc" in c or "narr" in c or "particular" in c), None)
            amount_col = next((c for c in df.columns if "amount" in c or "val" in c), None)

            if date_col and desc_col and amount_col:
                for _, row in df.iterrows():
                    raw_records.append({
                        "date": str(row[date_col]).strip(),
                        "description": str(row[desc_col]).strip(),
                        "amount": abs(float(row[amount_col]))
                    })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse CSV statement: {str(e)}")

    # 2. Process PDF Files
    elif filename.endswith(".pdf"):
        try:
            raw_records = extract_transactions_from_pdf(contents)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF statement: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a .csv or .pdf file.")

    if not raw_records:
        raise HTTPException(status_code=400, detail="No valid transaction rows could be extracted from the file.")

    # 3. Hybrid Categorization & Vector Database Ingestion
    records = []
    for item in raw_records:
        try:
            # Enforce dayfirst=True to accurately parse Indian/UK standard DD/MM/YYYY dates
            parsed_date = pd.to_datetime(item["date"], dayfirst=True).strftime('%Y-%m-%d')
            desc = item["description"]
            amount = item["amount"]

            category, is_avoidable, embedding = categorizer.process_transaction(user_id, desc, amount)

            records.append({
                "user_id": user_id,
                "date": parsed_date,
                "description": desc,
                "amount": amount,
                "category": category,
                "is_avoidable": is_avoidable,
                "source": "pdf" if filename.endswith(".pdf") else "csv",
                "embedding": embedding
            })
        except Exception:
            continue

    if records:
        supabase.table("transactions").insert(records).execute()
        return {
            "message": f"Successfully imported {len(records)} transactions from {file.filename}",
            "count": len(records)
        }

    return {"message": "No valid transaction records were saved.", "count": 0}


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    limit: int = Query(50, ge=1, le=200),
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id_from_header(authorization)
    res = supabase.table("transactions").select("*").eq("user_id", user_id).order("date", desc=True).limit(limit).execute()
    return res.data or []


@router.patch("/correct-category")
def correct_category(
    correction: CategoryCorrection,
    authorization: Optional[str] = Header(None)
):
    user_id = get_user_id_from_header(authorization)
    
    tx = supabase.table("transactions").select("*").eq("id", correction.transaction_id).eq("user_id", user_id).execute()
    if not tx.data:
        raise HTTPException(status_code=404, detail="Transaction record not found")
    
    desc = tx.data[0]["description"]
    new_embedding = generate_embedding_with_retry(desc)
    
    update_payload = {
        "category": correction.new_category,
        "is_avoidable": correction.is_avoidable,
        "embedding": new_embedding
    }
    
    res = supabase.table("transactions").update(update_payload).eq("id", correction.transaction_id).execute()
    return {"message": "Category updated and model vector example saved", "data": res.data}