# SatQuery Python API (Dev 1 — GeoTIFF I/O + preview)

## Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Azure Container Apps

From the repository root, with Azure CLI installed and signed in (`az login`), deploy with:

```powershell
./backend/deploy-azure.ps1 -AppName <unique-app-name> -ResourceGroup <resource-group> -Location centralindia
```

`backend/Dockerfile` builds the API with its CPU model dependencies and the three configured checkpoints from `backend/checkpoints/`. The deploy script stages the required backend files into a temporary build context, then creates or updates the Container App with external ingress on port 8000. Azure CLI's `containerapp` extension may be installed on first use.

Before using the deployed API, configure production app settings in the Container App's **Secrets** and **Environment variables**. At minimum, set `DATABASE_URL` to a reachable production database (for example, Azure Database for PostgreSQL using an async SQLAlchemy URL); the default SQLite database is ephemeral in a container. Configure `CLERK_JWKS_URL`, `CLERK_ISSUER`, and `CORS_ORIGINS` for your production frontend. Add `GEMINI_API_KEY` or configure Vertex credentials, and `GCS_BUCKET` plus Google Cloud credentials if using GCS storage. Set optional ElevenLabs values only if enabling speech features. Keep secret values in Container Apps secrets and reference them from environment variables; do not put them in the image or commit them.

The checkpoints in `backend/checkpoints/` are baked into the image. To change a checkpoint, rebuild and redeploy. The VLM URL is optional and remains disabled when `SATQUERY_VLM_URL` is empty.

## Endpoints

- `GET /health`
- `POST /preview` — multipart `file` → preview PNG + metadata
- `POST /compatibility` — multipart `file` + form `job=ask_scene`

Accepted: `.tif` `.tiff` (preferred), `.png` `.jpg` `.jpeg` (benchmark only).
