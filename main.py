import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from simulation_engine import model_health, run_simulation

app = FastAPI(
    title="BIT Anaerobic Biorefinery API",
    version="0.2.0",
    description="PyADM1ODE/ADM1da API for the BIT virtual process-study website."
)

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "https://bit-anaerobic-biorefinery.vercel.app"
)
origins = [origin.strip() for origin in frontend_origin.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    feed_rate_kg_day: float = Field(gt=0, le=100000)
    food_share_pct: float = Field(ge=0, le=100)
    garden_share_pct: float = Field(ge=0, le=100)
    temperature_c: float = Field(ge=0, le=80)
    hrt_days: float = Field(gt=0, le=365)
    duration_days: int = Field(ge=1, le=90)
    timestep_hours: int = Field(ge=1, le=24)

@app.get("/")
def root():
    return {
        "service": "BIT Anaerobic Biorefinery API",
        "status": "running",
        "model": model_health()
    }

@app.get("/api/health")
def health():
    return model_health()

@app.post("/api/simulate")
def simulate(request: SimulationRequest):
    try:
        return run_simulation(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected simulation error. Check backend logs.") from exc
