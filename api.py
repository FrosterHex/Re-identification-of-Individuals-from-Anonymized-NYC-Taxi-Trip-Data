from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os

from attack_logic import run_attack
from config import TARGET_TRIPS

app = FastAPI(title="NYC Taxi Cyber UI Backend")

# Enable CORS for React frontend (Vite default port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttackRequest(BaseModel):
    target_lat: float
    target_lon: float
    target_time: str
    radius_m: float = 250.0
    window_min: int = 15
    crack_hack_license: bool = False
    cloak_precision: int | None = None
    is_salted: bool = False

# Pre-load data to save time (similar to Streamlit's @st.cache_data)
DATA_FILE = "taxi_data.csv"
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame()

@app.get("/api/targets")
def get_targets():
    return {"targets": TARGET_TRIPS}

@app.post("/api/attack")
def execute_attack(req: AttackRequest):
    if df.empty:
        raise HTTPException(status_code=500, detail="Data file not found. Please run mock_data.py first.")
    
    try:
        result = run_attack(
            df=df,
            target_lat=req.target_lat,
            target_lon=req.target_lon,
            target_time=req.target_time,
            radius_m=req.radius_m,
            window_min=req.window_min,
            crack_hack_license=req.crack_hack_license,
            cloak_precision=req.cloak_precision,
            is_salted=req.is_salted
        )
        
        # Convert pandas dataframe to dict for JSON serialization
        if result["success"]:
            result["matched_trips"] = result["matched_trips"].fillna("").to_dict(orient="records")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
