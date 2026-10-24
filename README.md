# BIT Anaerobic Biorefinery API

Python API for the BIT Smart Campus virtual process-study website.

## Runtime options

- The repository retains a FastAPI app in `main.py` for an ASGI host (for example, a Render Web Service).
- The `api/health.py` and `api/simulate.py` handlers expose the same endpoints as Vercel Python functions, so the frontend can use its own Vercel origin without a separate paid server.
- `simulation_engine.py` is the shared PyADM1ODE/ADM1da adapter used by both deployments.

## Endpoints

- `GET /api/health`: reports API health and the installed `pyadm1` package version. It does not execute a simulation.
- `POST /api/simulate`: validates input, runs PyADM1ODE/ADM1da, and returns gas, methane, pH, VFA, and TAC outputs plus model assumptions.

Example JSON body:

```json
{
  "feed_rate_kg_day": 600,
  "food_share_pct": 55,
  "garden_share_pct": 15,
  "temperature_c": 37,
  "hrt_days": 25,
  "duration_days": 30,
  "timestep_hours": 6
}
```

## Scientific limitations

The UI inputs do not characterize the campus waste. The adapter maps:
- the food share to the built-in `onion_waste` substrate proxy;
- the garden share to the built-in `grass_silage` substrate proxy;
- the remaining share to the built-in `maize_silage_milk_ripeness` proxy.

It converts kg/day into m³/day using an assumed bulk density of 1000 kg/m³ and sizes the liquid reactor as flow × requested HRT, with a gas headspace ratio taken from the PyADM1ODE basic example. These are explicit modelling assumptions, not measured BIT feedstock properties. Outputs must not be presented as validated BIT predictions.

The simulation endpoint returns an error if the real model fails. It never substitutes the website's illustrative screening heuristic as a successful PyADM1ODE result.

## Local ASGI run

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Vercel

Keep the existing HTML frontend and deploy the repository using its connected GitHub project. The Vercel Python runtime supports functions under `api/`. After deployment, test:
- `https://YOUR-VERCEL-DOMAIN/api/health`
- The website's **Check backend** control.

If the Vercel project has a custom framework preset that prevents Python function discovery, review the deployment build log before changing the frontend project settings.

## Optional Supabase cloud records

The repository includes an opt-in, per-user Supabase storage foundation. Follow [SUPABASE_SETUP.md](SUPABASE_SETUP.md) to create a free-tier project, apply the RLS-protected schema in `supabase/migrations/`, configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Vercel, and enable manual sign-in and cloud sync. The browser retains its local data; cloud upload and merge-back are explicit user actions. Never expose a Supabase service-role key.
