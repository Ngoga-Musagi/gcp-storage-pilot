# GCP Storage AI Agent — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENTS / INTERFACES                       │
│                                                                 │
│   Browser UI          Claude Code / Cursor       CLI            │
│  (localhost:3000)     (MCP Tools)             (adk run)         │
└────────┬──────────────────────┬────────────────────┬────────────┘
         │ Socket.IO            │ stdio (MCP)         │ stdin
         ▼                      ▼                     │
┌─────────────────┐   ┌──────────────────┐           │
│  NestJS BFF     │   │  mcp_server.py   │           │
│  (port 3000)    │   │  (FastMCP)       │           │
│  chat.gateway   │   │                  │           │
│  chat.service   │   │  3 MCP Tools:    │           │
└────────┬────────┘   │  • gcs_command   │           │
         │ HTTP POST  │  • deploy_website│           │
         │ /api/chat  │  • enable_hosting│           │
         └──────┬─────┴─────────┬────────┘           │
                │               │ HTTP POST /api/chat │
                ▼               ▼                     ▼
        ┌─────────────────────────────────────────────────┐
        │              FastAPI Backend (port 8080)         │
        │                    app.py                        │
        │                                                  │
        │  POST /api/chat    POST /api/deploy              │
        │  POST /api/upload  GET  /api/health              │
        └──────────────────────┬──────────────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────────┐
        │              ADK Runner                          │
        │         (InMemorySessionService)                 │
        └──────────────────────┬──────────────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────────┐
        │           Gemini 2.5 Flash (Agent)               │
        │                 agent.py                         │
        │                                                  │
        │  Reads user intent → selects the right tool(s)  │
        │  Chains multiple tools for complex tasks         │
        │  Returns natural language response               │
        └──────────────────────┬──────────────────────────┘
                               │  calls 1..N tools per request
                               ▼
        ┌─────────────────────────────────────────────────┐
        │            81 GCS Tool Functions                 │
        │                 tools.py                         │
        │                                                  │
        │  Bucket Ops (8)    Object Mgmt (10)              │
        │  Permissions (10)  Monitoring (8)                │
        │  Website (7)       Advanced Ops (9)              │
        │  Retention (3)     Object Holds (5)              │
        │  Encryption (3)    Pub/Sub (3)                   │
        │  Soft Delete (4)   Batch Ops (3)                 │
        │  Resumable (1)     Inventory (2)                 │
        └──────────────────────┬──────────────────────────┘
                               │
                               ▼
        ┌─────────────────────────────────────────────────┐
        │         Google Cloud Platform APIs               │
        │                                                  │
        │  Cloud Storage    BigQuery    Cloud Monitoring   │
        │  Pub/Sub          IAM         Cloud Functions    │
        └─────────────────────────────────────────────────┘
```

---

## Why 3 MCP Tools, Not 81

This is the most important architectural decision in the system.

### The Problem With Exposing All 81 Tools

When an AI coding assistant (Claude Code, Cursor) makes tool calls, it must:
1. Choose the right tool from the list
2. Know the exact parameters
3. Handle multi-step sequences itself
4. Manage errors between steps

Exposing 81 tools pushes all of that reasoning onto the coding assistant — which is a general-purpose coding LLM, not a GCS specialist.

**Example task:** *"Archive objects older than 30 days and notify me via Pub/Sub"*

With 81 tools exposed, Cursor must reason across all of them, pick the right combination, know the exact parameter names, and chain them manually. It was not trained to be a GCS expert.

With 3 MCP tools, Cursor calls one thing:

```
gcs_command("archive objects older than 30 days and notify via Pub/Sub")
```

Gemini (a GCS specialist by training and system prompt) then internally selects and chains:
1. `set_bucket_lifecycle_rules(age=30, action=ARCHIVE)`
2. `create_bucket_notification(topic="...")`

And returns a single natural language result.

### The Layered Intelligence Design

```
General AI (Claude Code / Cursor)
    ↓  understands developer intent
gcs_command()  ←  single MCP entry point
    ↓  routes to the specialist
Gemini 2.5 Flash  ←  GCS domain expert
    ↓  selects + chains tools autonomously
81 GCS functions  ←  precise authenticated API calls
    ↓
Google Cloud Storage
```

Each layer does what it is best at:

| Layer | Role |
|---|---|
| Claude / Cursor | Understands developer intent, writes code, manages project context |
| Gemini 2.5 Flash | Understands GCS semantics, selects right tools, chains multi-step workflows |
| 81 tool functions | Execute precise, authenticated GCS API calls — no reasoning required |

### The 3 MCP Tools and Why They Were Chosen

| MCP Tool | Why It Is a Dedicated Tool |
|---|---|
| `gcs_command(instruction)` | Universal gateway — any natural language GCS operation routes through here |
| `deploy_website(bucket, html)` | Coding agents building websites need a structured, typed interface — raw HTML in, public URL out. `gcs_command` could do it, but the explicit signature makes agent code cleaner |
| `enable_website_hosting(bucket)` | Frequently called as a standalone pre-flight step before deployment. Promoting it to a dedicated tool avoids ambiguity in agent workflows |

All other 78 tools remain internal to the Gemini agent. The coding assistant never needs to know they exist — it just describes what it wants, and Gemini picks them.

### When You Would Expose All 81 Tools

Only if the goal is to **bypass the agent entirely** — calling GCS functions directly as a typed SDK, without natural language routing. That is a fundamentally different product (a Python SDK wrapper) and not what this system is.

---

## Component Responsibilities

### mcp_server.py
- Runs as a background subprocess launched by Claude Code / Cursor
- Receives MCP tool calls over stdio
- Forwards them as HTTP POST to FastAPI `/api/chat` or `/api/deploy`
- Requires FastAPI to be running before tool calls are made

### app.py (FastAPI)
- Single HTTP entry point for all clients (browser, NestJS, MCP server)
- Manages ADK sessions (one per browser tab or agent session)
- Handles file uploads as in-memory multipart streams (no temp files on disk)
- Runs a warmup call on startup to prime Gemini's context cache

### agent.py (ADK Root Agent)
- Defines the system prompt with full GCS expertise
- Registers all 81 tools with the ADK Runner
- Gemini selects the right tools, chains them, and generates natural language responses
- Retries automatically if Gemini returns empty (quota edge case on first call)

### tools.py
- 81 pure Python functions, each calling GCS/BigQuery/Monitoring APIs directly
- **Active code starts at line 3914** (lines 1–3913 are legacy commented code — do not edit)
- Every function follows the same auth pattern and returns the same response schema
- Stateless — no shared state between tool calls

### storage-ui (NestJS)
- WebSocket BFF: browser connects via Socket.IO
- Proxies chat messages to FastAPI `/api/chat`
- Streams `thinking` → `response` events back to the browser in real time
- Contains no GCS logic — purely a transport layer

---

## Data Flow: Natural Language → GCS API

```
1. User types: "Enable versioning on ngogabucketone1234"

2. Browser → Socket.IO → NestJS → POST /api/chat
   { "message": "Enable versioning on ngogabucketone1234", "session_id": "abc" }

3. FastAPI → ADK Runner → Gemini 2.5 Flash
   Gemini selects: enable_versioning(bucket_name="ngogabucketone1234")

4. tools.py: enable_versioning()
   - Reads GOOGLE_CLOUD_PROJECT, GOOGLE_APPLICATION_CREDENTIALS
   - Creates storage.Client with service account credentials
   - bucket.versioning_enabled = True; bucket.patch()
   - Returns { "status": "success", "message": "Versioning enabled", ... }

5. Gemini formats the tool result as natural language

6. FastAPI → NestJS → Socket.IO → Browser
   "Versioning has been successfully enabled on ngogabucketone1234."
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Agent Framework | Google ADK 1.16 | Tool orchestration, session management, Gemini integration |
| LLM | Gemini 2.5 Flash | Best-in-class tool selection, 1M token context, free tier available |
| Backend | FastAPI + Uvicorn | Async, fast, supports WebSocket and multipart uploads |
| BFF | NestJS 10 + Socket.IO | Real-time UI with event streaming |
| MCP Server | FastMCP (Python) | stdio transport, zero-config discovery by Claude Code / Cursor |
| GCP SDKs | google-cloud-storage, monitoring, bigquery | Direct API access, no REST overhead |
| Auth | Service Account + ADC | Works locally and in Cloud Run |
