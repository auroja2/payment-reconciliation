@app.get("/download/platform")
def download_platform_csv():
    path = "platform_test_data.csv"
    if not Path(path).exists():
        # Generate if missing
        data = generate_datasets(40)
        import pandas as pd
        pd.DataFrame(data["platform"]).to_csv(path, index=False)
    return FileResponse(path, media_type="text/csv", filename=path)

from __future__ import annotations
"""FastAPI reconciliation service."""

@app.get("/download/bank")
def download_bank_csv():
    path = "bank_test_data.csv"
    if not Path(path).exists():
        # Generate if missing
        data = generate_datasets(40)
        import pandas as pd
        pd.DataFrame(data["bank"]).to_csv(path, index=False)
    return FileResponse(path, media_type="text/csv", filename=path)

from __future__ import annotations
"""FastAPI reconciliation service."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from generator import generate_datasets
from reconciler import reconcile

app = FastAPI(title="Payment Reconciliation API", version="1.0.0")

# Serve static frontend files
FRONTEND_DIR = Path(__file__).parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_frontend():
    """Serve the frontend UI."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to Payment Reconciliation API. Visit /docs for API documentation."}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store (replace with DB in prod)
_store: dict = {"platform": [], "bank": [], "report": None}


# ── Models ────────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    num_txns: int = 40


class ManualDataset(BaseModel):
    platform: list[dict]
    bank: list[dict]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/generate")
def generate(req: GenerateRequest = None):
    if req is None:
        req = GenerateRequest()
    data = generate_datasets(req.num_txns)
    _store["platform"] = data["platform"]
    _store["bank"] = data["bank"]
    _store["report"] = None
    return {"message": f"Generated {len(data['platform'])} platform and {len(data['bank'])} bank transactions.",
            "platform_count": len(data["platform"]),
            "bank_count": len(data["bank"])}


@app.post("/reconcile")
def run_reconcile():
    if not _store["platform"] and not _store["bank"]:
        raise HTTPException(400, "No data. Call /generate first.")
    report = reconcile(_store["platform"], _store["bank"])
    _store["report"] = report
    return report


@app.get("/report")
def get_report():
    if _store["report"] is None:
        raise HTTPException(404, "No report available. Call /reconcile first.")
    return _store["report"]


@app.get("/transactions")
def get_transactions():
    return {"platform": _store["platform"], "bank": _store["bank"]}


# Export generated test data as CSV
@app.get("/export-test-data")
def export_test_data():
    import pandas as pd
    platform = _store["platform"]
    bank = _store["bank"]
    if not platform or not bank:
        # Generate if not present
        data = generate_datasets(40)
        platform = data["platform"]
        bank = data["bank"]
    platform_df = pd.DataFrame(platform)
    bank_df = pd.DataFrame(bank)
    platform_path = "platform_test_data.csv"
    bank_path = "bank_test_data.csv"
    platform_df.to_csv(platform_path, index=False)
    bank_df.to_csv(bank_path, index=False)
    return {"platform_csv": platform_path, "bank_csv": bank_path}


@app.get("/health")
def health():
    return {"status": "ok"}
