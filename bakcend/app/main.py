from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import risk,dashboard,transactions,advisory,knowledge

app = FastAPI(title="FINMATE API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(risk.router)
app.include_router(advisory.router)
app.include_router(knowledge.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "FINMATE"}