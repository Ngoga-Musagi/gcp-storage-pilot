# GCP Storage Pilot — AI-Powered Cloud Storage Agent

Manage Google Cloud Storage through natural language. Built with **Google ADK**, **Gemini 2.5 Flash**, **FastAPI**, and **NestJS**.

## Architecture

```
Browser (localhost:3000)
  ↕ Socket.IO
NestJS BFF (storage-ui/, port 3000)
  ↕ HTTP
FastAPI Backend (bucket_storage_agent/, port 8080)
  ↕ ADK Runner
Gemini 2.5 Flash + 81 GCS Tools
  ↕
Google Cloud Storage API
```

## Setup

### 1. Python environment

```bash
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash
# source venv/bin/activate          # Linux/Mac
pip install -r bucket_storage_agent/requirements.txt
```

### 2. GCP credentials

Place your service account key at `bucket_storage_agent/service-account-key.json`.

Create `bucket_storage_agent/.env`:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-gemini-api-key
```

Verify auth:
```bash
python bucket_storage_agent/test_auth.py
```

### 3. NestJS UI

```bash
cd storage-ui && npm install && cd ..
```

## Running

**Terminal 1 — Backend (port 8080)**
```bash
source venv/Scripts/activate
uvicorn bucket_storage_agent.app:app --host 0.0.0.0 --port 8080 --reload
```

**Terminal 2 — UI (port 3000)**
```bash
cd storage-ui && npm run start:dev
```

Open **http://localhost:3000**.

### Alternatives

```bash
# ADK built-in web UI (port 8000)
adk web bucket_storage_agent

# CLI only
adk run bucket_storage_agent
```

## MCP Integration (Claude Code / Cursor)

`.mcp.json` at the project root auto-configures tools for Claude Code.

| Tool | Description |
|------|-------------|
| `gcs_command(instruction)` | Natural language GCS command |
| `deploy_website(bucket, index_html)` | Deploy HTML to a GCS bucket |
| `enable_website_hosting(bucket)` | Enable static hosting |

For Cursor/Windsurf, add to MCP settings:
```json
{
  "command": "python",
  "args": ["bucket_storage_agent/mcp_server.py"],
  "cwd": "/path/to/gcp-storage-pilot",
  "env": { "AGENT_API_URL": "http://localhost:8080" }
}
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No response from agent` | Ensure FastAPI started cleanly — check logs for "ADK and agent loaded successfully" |
| Website hosting 403 | Wait 1–2 min for IAM propagation |
| 429 RESOURCE_EXHAUSTED | Switch to `gemini-1.5-flash` in `agent.py` (1500 req/day free tier) |
| NestJS "Disconnected" | Ensure both servers are running on ports 3000 and 8080 |
| `ImportError: attempted relative import` | Run uvicorn from the project root, not inside the `bucket_storage_agent/` folder |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | Google ADK |
| LLM | Gemini 2.5 Flash |
| Backend | FastAPI + Uvicorn |
| Frontend | NestJS 10 + TypeScript + Socket.IO |
| GCP SDKs | google-cloud-storage, monitoring, bigquery |

## License

MIT — Ngoga Alexis
