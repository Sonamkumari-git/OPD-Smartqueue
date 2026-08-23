# Render Deployment Guide

OPD SmartQueue is deployed as two Render services: a static React application and a Python FastAPI web service. MongoDB is deliberately external to Render because the application requires a durable MongoDB Community-compatible connection string; use a managed MongoDB provider such as MongoDB Atlas rather than an ephemeral local database.

| Render service | Source | Build / start | Required configuration |
|---|---|---|---|
| `opd-smartqueue-api` | `backend/` | `pip install -r requirements.txt` / `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | `MONGODB_URL`, `FRONTEND_URL`, generated `JWT_SECRET` |
| `opd-smartqueue-web` | repository root | `pnpm install --frozen-lockfile && pnpm build` | `VITE_API_BASE_URL` set to the API’s public HTTPS URL |

## First deployment

Create a MongoDB Atlas deployment and database user, restrict the user to the `opd_queue_management` database, and retain its TLS connection string. In Render, choose **New → Blueprint**, select this GitHub repository, and import `render.yaml`. Before applying the Blueprint, supply `MONGODB_URL` for the API service. After the API receives its public URL, set `FRONTEND_URL` to the static site’s HTTPS URL and set `VITE_API_BASE_URL` to the API’s HTTPS URL; then trigger a frontend redeploy so Vite embeds the correct API base.

## Production initialization

After the API is live and can reach MongoDB, run the initialization workflow from a trusted terminal with the same production `MONGODB_URL` and a secure `JWT_SECRET`. Do not seed demonstration accounts in a public production deployment.

```bash
cd backend
APP_ENV=production MONGODB_URL='mongodb+srv://…' JWT_SECRET='at-least-32-random-characters' \
python -m scripts.init_db
```

Use `/health` for process health and `/ready` to confirm the API has MongoDB connectivity. The application will deliberately refuse a production startup if `JWT_SECRET` is unset, is the development default, or has fewer than 32 characters.

## Operational notes

The current WebSocket manager holds channels in process memory. It works for a single Render web instance. If Render is later scaled to multiple API instances, introduce a shared pub/sub transport before relying on cross-instance realtime delivery. The frontend must never contain `MONGODB_URL`, `JWT_SECRET`, or other server secrets.
