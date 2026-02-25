# KORAIL AX Platform API Specifications

This document defines the RESTful and gRPC API endpoints for the KORAIL AX Platform backend and AI Services. The API Gateway (Spring Boot) proxies most `/api/v1/ai/*` requests to the Python AI Core (`FastAPI`).

---

## 1. Module 01: Common Tasks AI (RAG & Documents)

### 1.1 `POST /api/v1/documents/upload`
Upload a HWP, PDF, or Word document for vector embedding.
*   **Request:** `multipart/form-data` with file bytes.
*   **Response:** `{"document_id": "uuid", "status": "processing"}`

### 1.2 `GET /api/v1/documents/status/{document_id}`
Check the vector indexing status of a document.
*   **Response:** `{"document_id": "uuid", "status": "completed", "chunks_indexed": 45}`

### 1.3 `POST /api/v1/ai/chat/query`
Ask the AI assistant a question based on uploaded documents.
*   **Target:** Routed to FastAPI AI Service.
*   **Request Body:**
    ```json
    {
      "query": "최근 변경된 송전선로 이격거리 규정은 무엇인가요?",
      "filters": { "department": "전철전력처", "doc_type": "규정" }
    }
    ```
*   **Response:**
    ```json
    {
      "answer": "...",
      "sources": [
        {"doc_id": "...", "snippet": "...", "confidence": 0.95}
      ]
    }
    ```

---

## 2. Module 02: Design Tasks AI (CAD & Layout)

### 2.1 `POST /api/v1/ai/design/parse`
Extract structured design parameters from a natural language specification.
*   **Target:** Routed to FastAPI.
*   **Request Body:** `{"text": "154kV 옥외 변전소 설계해주세요. 주변압기 150MVA..."}`
*   **Response:** `{"parameters": {"voltage": "154kV", "transformer_capacity": "150MVA", "type": "outdoor"}}`

### 2.2 `POST /api/v1/ai/design/generate-cad`
Generate a DWG CAD file based on extracted parameters.
*   **Target:** Routed to FastAPI (utilizing AutoCAD engine/python bindings).
*   **Request Body:** `{"parameters": {...}, "approval_id": "uuid"}`
*   **Response:** `{"cad_file_url": "s3/minio/path/to/generated.dwg", "status": "success", "warnings": []}`

---

## 3. Module 03: Construction Tasks AI (Safety & Contracts)

### 3.1 `POST /api/v1/ai/safety/analyze-video`
Analyze a construction site video stream (RTSP URL) or clip for safety violations.
*   **Request Body:** `{"video_url": "rtsp://...", "check_items": ["helmet", "safety_belt", "live_wire_distance"]}`
*   **Response:** `{"job_id": "uuid", "status": "running"}`

### 3.2 `GET /api/v1/ai/safety/alerts/{job_id}`
Retrieve detected safety violations for a video analysis job.
*   **Response:**
    ```json
    {
      "alerts": [
        {"timestamp": "00:01:23", "type": "helmet_missing", "bounding_box": [x,y,w,h], "severity": "HIGH"}
      ]
    }
    ```

### 3.3 `POST /api/v1/ai/contracts/risk-assessment`
Generate a draft safety risk assessment document based on construction type.
*   **Request Body:** `{"construction_type": "변전설비_가압", "location": "수도권"}`
*   **Response:** `{"draft_document_url": "...", "auto_identified_risks": ["감전", "추락"]}`

---

## 4. Module 04: SCADA AI (Predictive Maintenance & Control)

### 4.1 `POST /api/v1/scada/ingest`
Ingest real-time SCADA telemetry for anomaly detection.
*   **Protocol:** High-throughput (gRPC or Kafka preferred, REST for testing).
*   **Request Body:** `{"station_id": "SS001", "timestamp": "2026-02-25T10:00:00Z", "voltage": 154.2, "current": 450}`
*   **Response:** `200 OK`

### 4.2 `GET /api/v1/ai/scada/anomalies/active`
Retrieve currently active anomalies detected by the LSTM Autoencoder.
*   **Response:**
    ```json
    {
      "active_anomalies": [
        {
          "station_id": "SS001",
          "reconstruction_error": 5.4,
          "sigma": 3.2,
          "predicted_component_failure": "유입변압기",
          "recommended_action": "부하율 85% 초과, 인접 변전소 SS002로 부하 분산 요망"
        }
      ]
    }
    ```

### 4.3 `POST /api/v1/ai/scada/action/approve`
Human-in-the-loop (HIL) approval for an AI-recommended SCADA action.
*   **Request Body:** `{"anomaly_id": "uuid", "action": "EXECUTE", "operator_id": "sungjaekang"}`
*   **Response:** `{"status": "command_sent_to_scada_gateway"}`
