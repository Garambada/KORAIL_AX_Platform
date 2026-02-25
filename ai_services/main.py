from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random
import datetime

app = FastAPI(
    title="KORAIL AX Platform - AI Services PoC",
    description="Proof of Concept for SCADA AI Anomaly Detection (Module 04)"
)

# === Mock Data Stores ===
scada_telemetry_db = []
active_anomalies_db = []

# === Pydantic Models ===
class ScadaTelemetry(BaseModel):
    station_id: str
    timestamp: str
    voltage: float
    current: float

class AnomalyEvent(BaseModel):
    anomaly_id: str
    station_id: str
    timestamp: str
    reconstruction_error: float
    sigma: float
    predicted_component_failure: str
    recommended_action: str

class ApprovalRequest(BaseModel):
    anomaly_id: str
    action: str
    operator_id: str

# === API Endpoints ===

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "korail_ai_core"}

@app.post("/api/v1/scada/ingest")
def ingest_telemetry(data: ScadaTelemetry):
    """
    Ingest real-time SCADA telemetry.
    In a real scenario, this would trigger an LSTM Autoencoder prediction.
    For this PoC, we occasionally inject a mock anomaly.
    """
    scada_telemetry_db.append(data)
    
    # Mock LSTM Anomaly Detection Logic (Randomized for PoC)
    if random.random() > 0.8:  # 20% chance of an anomaly
        anomaly = AnomalyEvent(
            anomaly_id=f"ANOM-{random.randint(1000, 9999)}",
            station_id=data.station_id,
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            reconstruction_error=round(random.uniform(3.5, 7.0), 2),
            sigma=round(random.uniform(3.0, 5.0), 1),
            predicted_component_failure="유입변압기 절연유 열화 의심",
            recommended_action=f"인접 변전소로 부하 분산 요망 (현재 부하율 초과 위험)"
        )
        active_anomalies_db.append(anomaly)
        return {"status": "ingested", "anomaly_detected": True, "anomaly_id": anomaly.anomaly_id}
        
    return {"status": "ingested", "anomaly_detected": False}

@app.get("/api/v1/ai/scada/anomalies/active", response_model=List[AnomalyEvent])
def get_active_anomalies():
    """
    Retrieve currently active anomalies.
    """
    return active_anomalies_db

@app.post("/api/v1/ai/scada/action/approve")
def approve_scada_action(req: ApprovalRequest):
    """
    Human-in-the-loop (HIL) approval for an AI-recommended SCADA action.
    """
    global active_anomalies_db
    print(req)
    # Find anomaly
    anomaly = next((a for a in active_anomalies_db if a.anomaly_id == req.anomaly_id), None)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly ID not found")
        
    if req.action == "EXECUTE":
        # Remove from active anomalies (resolved)
        active_anomalies_db = [a for a in active_anomalies_db if a.anomaly_id != req.anomaly_id]
        return {
            "status": "command_sent_to_scada_gateway", 
            "message": f"Operator {req.operator_id} approved action for {req.anomaly_id}"
        }
    elif req.action == "REJECT":
        # Remove from active anomalies (ignored)
        active_anomalies_db = [a for a in active_anomalies_db if a.anomaly_id != req.anomaly_id]
        return {
            "status": "action_rejected",
            "message": f"Operator {req.operator_id} rejected action for {req.anomaly_id}"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use EXECUTE or REJECT.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
