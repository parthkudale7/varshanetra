"""
Stage 7 of the roadmap. Run from the project root with:

    pip install fastapi uvicorn
    uvicorn api.main:app --reload --port 8000

Not runnable inside the sandbox this was built in (no internet there
to install fastapi) - predict_service.py and api/data_feed.py under
this are already tested directly, this file is just the HTTP wrapper
around them.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from predict_service import predict
from api.data_feed import get_history, list_wards, DEFAULT_MODE

app = FastAPI(title="Varshanetra API", version="0.1.0")


class PredictRequest(BaseModel):
    ward: str
    mode: str = DEFAULT_MODE


@app.get("/")
def root():
    return {
        "name": "Varshanetra API",
        "version": "0.1.0",
        "description": "Flood prediction API for Pune wards",
        "endpoints": {
            "GET /": "This page",
            "GET /health": "Health check",
            "GET /wards": "List all supported wards",
            "POST /predict": "Predict rainfall & flood risk (body: {ward, mode})",
            "GET /demo/predict/{ward}": "Quick demo prediction for a ward",
            "GET /docs": "Interactive API documentation (Swagger UI)",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/wards")
def wards():
    return {"wards": list_wards()}


@app.post("/predict")
def predict_endpoint(req: PredictRequest):
    if req.ward not in list_wards():
        raise HTTPException(status_code=404, detail=f"unknown ward '{req.ward}'")
    try:
        history = get_history(req.ward, mode=req.mode)
        return predict(req.ward, history)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.get("/demo/predict/{ward}")
def demo_predict(ward: str):
    """Convenience GET version, always demo mode - handy for a quick browser check."""
    if ward not in list_wards():
        raise HTTPException(status_code=404, detail=f"unknown ward '{ward}'")
    history = get_history(ward, mode="demo")
    return predict(ward, history)
