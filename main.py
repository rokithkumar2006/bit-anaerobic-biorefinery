import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="BIT Anaerobic Biorefinery API", version="0.1.0")

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "https://bit-anaerobic-biorefinery.vercel.app"
)
origins = [x.strip() for x in frontend_origin.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    feed_rate_kg_day: float = Field(gt=0)
    food_share_pct: float = Field(ge=0, le=100)
    garden_share_pct: float = Field(ge=0, le=100)
    temperature_c: float = Field(ge=0, le=80)
    hrt_days: float = Field(gt=0, le=365)
    duration_days: int = Field(ge=1, le=365)
    timestep_hours: int = Field(ge=1, le=24)

@app.get("/")
def root():
    return {
        "service": "BIT Anaerobic Biorefinery API",
        "status": "running",
        "note": "Starter API only; PyADM1ODE is not yet integrated."
    }

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine": "backend-starter-no-model",
        "model_integrated": False
    }

@app.post("/api/simulate")
def simulate(request: SimulationRequest):
    # Fail safely rather than fabricate mechanistic-model output.
    raise HTTPException(
        status_code=501,
        detail=(
            "PyADM1ODE is not integrated yet. The backend is reachable, "
            "but no mechanistic simulation has been run."
        ),
    )
