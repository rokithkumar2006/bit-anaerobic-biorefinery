# BIT Anaerobic Biorefinery — Render backend starter

This package creates a small FastAPI service for deployment on Render.

## Important limitation

This is NOT yet the PyADM1ODE model. `/api/health` can verify that the API is online, but `/api/simulate` deliberately returns HTTP 501 until the actual PyADM1ODE source is installed and its real interface is verified. It does not fabricate ADM1 outputs.

## Deploy

1. In Render, choose New → Web Service and connect this repository.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set `FRONTEND_ORIGIN` to `https://bit-anaerobic-biorefinery.vercel.app`.
5. After deployment, open `https://YOUR-RENDER-SERVICE.onrender.com/api/health`.

The health response should contain `"status": "ok"` and `"model_integrated": false`.

## Before using the model panel

Add and test the actual PyADM1ODE source and its dependency/license requirements. Then replace the `/api/simulate` 501 response with a verified model adapter. Do not claim the model is integrated until a real simulation succeeds and units and outputs are checked.
