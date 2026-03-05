# GCP Cloud Storage AI Agent

An AI-powered Google Cloud Storage management agent built with Google ADK 1.16 and Gemini 2.5 Flash. Manage buckets, objects, IAM, website hosting, and cost optimization through natural language.

**Capstone Project** — Google Agents Intensive, Enterprise Track

---

## Features

- **Bucket & Object Management** — create, delete, list, upload, download, copy, rename, signed URLs
- **Security & IAM** — add/remove members, IAM policies, ACLs, uniform bucket-level access, audit access
- **Compliance & Data Protection** — retention policies, temporary holds, event-based holds, CMEK encryption
- **Soft Delete & Recovery** — enable soft delete (1–90 day window), list and restore soft-deleted objects
- **Pub/Sub Notifications** — trigger notifications on OBJECT_FINALIZE, OBJECT_DELETE, and other events
- **Direct File Upload** — browser file picker (any file type, drag & drop) → streams bytes to GCS, no local path needed
- **Batch & Scale Operations** — batch delete/copy, compose objects (parallel upload assembly), resumable uploads
- **Website Hosting** — enable static hosting, configure CORS, cache control, upload assets
- **Monitoring & Cost** — usage metrics, cost estimates, optimization recommendations, inventory reports
- **Advanced** — backup, migration, versioning, lifecycle rules, Cloud Functions, BigQuery integration

81 tools total.

---

## Setup

**Prerequisites:** Python 3.13, a GCP project with Cloud Storage API enabled, a service account with Storage Admin role.

```bash
# 1. Clone and enter the project
cd gcp-storage-pilot

# 2. Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate      # Linux/Mac

# 3. Install Python dependencies
pip install -r bucket_storage_agent/requirements.txt

# 4. Create .env in bucket_storage_agent/
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# 5. Place your service account JSON key at:
#    bucket_storage_agent/service-account-key.json

# 6. Verify credentials
python bucket_storage_agent/test_auth.py
```

---

## Running

### Full Stack — NestJS UI + FastAPI backend (recommended)

```bash
# Terminal 1 — FastAPI agent backend (port 8080)
cd gcp-storage-pilot
source venv/Scripts/activate
uvicorn bucket_storage_agent.app:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 — NestJS web UI (port 3000)
cd gcp-storage-pilot/storage-ui
npm install          # first time only
npm run start:dev

# Open http://localhost:3000
```

Optional — set `AGENT_API_URL` in `storage-ui/.env` if FastAPI runs on a different host:
```env
AGENT_API_URL=http://localhost:8080
```

### ADK Built-in Web UI (alternative)

```bash
cd gcp-storage-pilot
adk web bucket_storage_agent
# Open http://localhost:8000
```

### CLI only

```bash
cd gcp-storage-pilot
adk run bucket_storage_agent
```

---

## Architecture

```
Browser
  ↕ Socket.IO
NestJS  (storage-ui/, port 3000)
  ↕ HTTP
FastAPI (bucket_storage_agent/app.py, port 8080)
  ↕ ADK Runner
Root Agent — Gemini 2.5 Flash + 81 tools
  ↕
Google Cloud Storage API
```

Key files:

| File | Purpose |
|---|---|
| `agent.py` | Root ADK agent definition |
| `tools.py` | 81 GCS tool implementations (active code starts at line 3914) |
| `app.py` | FastAPI server — `/api/chat`, `/api/health`, WebSocket |
| `../storage-ui/` | NestJS BFF + Socket.IO gateway + static UI |

---

## Troubleshooting

**`No response from agent`** — ADK session wasn't created. Ensure FastAPI started cleanly (check logs for "ADK and agent loaded successfully").

**Website hosting 403** — IAM propagation takes 1–2 minutes after enabling. The tool automatically sets public access + CORS.

**429 RESOURCE_EXHAUSTED** — `gemini-2.5-flash` free tier is ~20 req/day. The agent surfaces the retry delay. Switch to `gemini-1.5-flash` in `agent.py` for higher quotas (1500 req/day).

**NestJS shows "Disconnected"** — Check both servers are running (ports 3000 and 8080). Check `AGENT_API_URL` env var.

**`ImportError: attempted relative import`** — Ensure `__init__.py` exists in `bucket_storage_agent/` and you're importing via `from bucket_storage_agent.agent import root_agent`.

---

## License

MIT — Copyright (c) 2024 Ngoga Alexis
