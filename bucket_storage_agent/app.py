"""
GCP Cloud Storage Management Agent — FastAPI Web Server

Serves the chat UI and handles WebSocket communication with the ADK agent.

Usage (from parent GCP-Cloudmate-ai/ directory):
    uvicorn bucket_storage_agent.app:app --host 0.0.0.0 --port 8080 --reload

Or directly:
    python -m bucket_storage_agent.app
"""

import asyncio
import json
import os
import re
import sys
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup — ensures bucket_storage_agent is importable as a package
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_project_root = _this_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Load .env — prefer the one in this directory, fall back to parent
_env_local = _this_dir / ".env"
_env_parent = _project_root / ".env"
if _env_local.exists():
    load_dotenv(_env_local)
elif _env_parent.exists():
    load_dotenv(_env_parent)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("gcs_agent_ui")

# ---------------------------------------------------------------------------
# ADK imports (after path setup and env load)
# ---------------------------------------------------------------------------
try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types
    from bucket_storage_agent.agent import root_agent
    ADK_AVAILABLE = True
    logger.info("ADK and agent loaded successfully")
except Exception as e:
    ADK_AVAILABLE = False
    root_agent = None
    logger.error(f"Failed to load ADK/agent: {e}")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GCS Management Agent UI",
    description="Natural language interface for Google Cloud Storage management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ADK singletons — created once, shared across all requests
# ---------------------------------------------------------------------------
_session_service: Optional[object] = None
_runner: Optional[object] = None

APP_NAME = "gcs_storage_ui"


def _get_session_service() -> Optional[object]:
    global _session_service
    if _session_service is None and ADK_AVAILABLE:
        _session_service = InMemorySessionService()
    return _session_service


def _get_runner() -> Optional[object]:
    """Return the shared Runner (created once). Runner is stateless — state lives in session_service."""
    global _runner
    if _runner is None and ADK_AVAILABLE:
        svc = _get_session_service()
        if svc is not None:
            _runner = Runner(
                agent=root_agent,
                app_name=APP_NAME,
                session_service=svc,
            )
    return _runner


# ---------------------------------------------------------------------------
# ASYNC session management
# ADK 1.16: InMemorySessionService.get_session() returns None (not raise)
# for missing sessions. Always check return value, not exceptions.
# ---------------------------------------------------------------------------
async def _ensure_session(session_id: str, user_id: str = "ui_user") -> None:
    """Create the ADK session if it doesn't exist."""
    svc = _get_session_service()
    if svc is None:
        return
    try:
        session = await svc.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        if session is None:
            await svc.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
            logger.info(f"Session created: {session_id[:8]}… user={user_id}")
    except Exception as exc:
        logger.warning(f"Session error ({session_id[:8]}): {exc}")


# ---------------------------------------------------------------------------
# ASYNC agent runner — runs directly in FastAPI's event loop
#
# WHY run_async() instead of run_in_executor(runner.run()):
#   runner.run() wraps run_async() by spawning a NEW thread with asyncio.run(),
#   which creates a fresh aiohttp ClientSession per call. The first Gemini API
#   call in any new ClientSession returns empty content (context-cache cold-start).
#   By using run_async() directly in the same FastAPI event loop, ALL calls share
#   ONE aiohttp session. The cold-start only affects the very first call (during
#   startup warmup), and the retry that follows immediately works correctly.
# ---------------------------------------------------------------------------
async def _run_agent_async(session_id: str, user_id: str, message: str) -> str:
    """Run the ADK agent async in the caller's event loop. Returns response text or "".

    Returns:
        - Non-empty string: agent response text
        - Empty string "":  Gemini returned no content (cold-start or throttle)
        - "Agent error: …": an exception occurred
        - "Rate limit: …":  429 RESOURCE_EXHAUSTED
    """
    runner = _get_runner()
    if runner is None:
        return (
            "Agent is not available. Check that ADK is installed and "
            "GOOGLE_APPLICATION_CREDENTIALS / GOOGLE_CLOUD_PROJECT are set correctly."
        )

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )

    response_parts: list[str] = []
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if hasattr(event, "is_final_response") and event.is_final_response():
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_parts.append(part.text)
    except Exception as e:
        err_str = str(e)
        logger.exception(f"Agent run error [{session_id[:8]}]")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            m = re.search(r"retry.*?(\d+)", err_str, re.IGNORECASE)
            delay = m.group(1) if m else "60"
            return (
                f"Rate limit reached for gemini-2.5-flash (free tier: ~20 req/day). "
                f"Please wait {delay} seconds and try again, "
                f"or switch to gemini-1.5-flash for higher quotas."
            )
        return f"Agent error: {e}"

    return "\n".join(response_parts) if response_parts else ""


# ---------------------------------------------------------------------------
# Startup warmup — prime the Gemini API HTTP connection + context cache
#
# The very first run_async() call to a fresh aiohttp session returns empty
# content (Gemini context-cache cold-start). We absorb this during startup
# so the first real user request is served by an already-warm connection.
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_warmup():
    """Make the first Gemini call during startup (empty response is fine here)."""
    if not ADK_AVAILABLE:
        return
    try:
        warmup_id = "warmup_" + str(uuid.uuid4())[:8]
        await _ensure_session(warmup_id, "warmup_user")
        result = await asyncio.wait_for(
            _run_agent_async(warmup_id, "warmup_user", "hello"),
            timeout=60.0,
        )
        logger.info(f"Warmup complete ({len(result)} chars) — Gemini connection primed")
    except Exception as exc:
        logger.warning(f"Warmup failed (non-fatal): {exc}")


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "ui_user"


class DeployFile(BaseModel):
    filename: str
    content: str


class DeployRequest(BaseModel):
    bucket_name: str
    files: list[DeployFile]
    session_id: Optional[str] = None
    user_id: Optional[str] = "deploy_user"


# ---------------------------------------------------------------------------
# HTTP Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main chat UI (plain HTML fallback — NestJS is the primary UI)."""
    ui_file = _this_dir / "ui" / "index.html"
    if not ui_file.exists():
        return HTMLResponse(
            "<h1>UI not found.</h1><p>Start the NestJS UI: <code>cd storage-ui && npm run start:dev</code></p>",
            status_code=404,
        )
    return HTMLResponse(content=ui_file.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    """Health check — returns agent and credential status."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "not set")
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "not set")
    creds_ok = Path(creds).exists() if creds != "not set" else False
    return {
        "status": "ok",
        "adk_available": ADK_AVAILABLE,
        "project": project,
        "credentials_file_exists": creds_ok,
        "model": getattr(root_agent, "model", "unknown") if root_agent else "N/A",
    }


@app.post("/api/session/new")
async def new_session():
    """Create a new chat session and return its ID."""
    session_id = str(uuid.uuid4())
    await _ensure_session(session_id)
    return {"session_id": session_id}


@app.post("/api/chat")
async def chat_http(request: ChatRequest):
    """REST endpoint — NestJS calls this for every chat message."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "ui_user"

    await _ensure_session(session_id, user_id)

    try:
        response = await asyncio.wait_for(
            _run_agent_async(session_id, user_id, request.message),
            timeout=180.0,
        )
    except asyncio.TimeoutError:
        response = (
            "Request timed out after 180 seconds. "
            "Complex operations (backup, migration) may take longer — try again."
        )

    # Cold-start retry: after the warmup's first empty response, the aiohttp
    # connection is established. Retry with a NEW session — the same session
    # would have a corrupted empty-model-response in its history, but a fresh
    # session benefits from the already-warm connection and works correctly.
    if not response:
        retry_id = str(uuid.uuid4())
        logger.info(f"Empty response [{session_id[:8]}] — retrying with fresh session [{retry_id[:8]}]…")
        await _ensure_session(retry_id, user_id)
        await asyncio.sleep(1)   # brief pause for connection to stabilise
        try:
            response = await asyncio.wait_for(
                _run_agent_async(retry_id, user_id, request.message),
                timeout=180.0,
            )
            if response:
                session_id = retry_id   # migrate client to the working session
        except asyncio.TimeoutError:
            response = "Request timed out. Try again."

    return JSONResponse({
        "response": response or "No response from agent. Please try again.",
        "session_id": session_id,
        "status": "success",
    })


@app.post("/api/deploy")
async def deploy_website(request: DeployRequest):
    """
    Programmatic website deployment endpoint.

    Accepts structured file content and drives the agent to upload each file
    to the specified GCS bucket using the upload_html_content tool.

    Callable by external coding agents (e.g. Claude Code, Cursor) via:
        POST /api/deploy
        { "bucket_name": "my-bucket", "files": [{"filename": "index.html", "content": "..."}] }
    """
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or "deploy_user"

    await _ensure_session(session_id, user_id)

    responses: list[str] = []

    for deploy_file in request.files:
        message = (
            f"Upload the following as {deploy_file.filename} "
            f"to bucket '{request.bucket_name}':\n"
            f"```html\n{deploy_file.content}\n```"
        )
        try:
            response = await asyncio.wait_for(
                _run_agent_async(session_id, user_id, message),
                timeout=120.0,
            )
        except asyncio.TimeoutError:
            response = f"Timed out uploading {deploy_file.filename}."

        # Cold-start retry with fresh session
        if not response:
            retry_id = str(uuid.uuid4())
            await _ensure_session(retry_id, user_id)
            await asyncio.sleep(1)
            try:
                response = await asyncio.wait_for(
                    _run_agent_async(retry_id, user_id, message),
                    timeout=120.0,
                )
                if response:
                    session_id = retry_id
            except asyncio.TimeoutError:
                response = f"Timed out uploading {deploy_file.filename} (retry)."

        responses.append(response or f"No response for {deploy_file.filename}.")

    return JSONResponse({
        "response": "\n\n---\n\n".join(responses),
        "session_id": session_id,
        "status": "success",
    })


# ---------------------------------------------------------------------------
# File upload endpoint — browser sends raw file bytes, we push to GCS directly
# No local file path needed: file is streamed from browser → FastAPI → GCS
# ---------------------------------------------------------------------------
@app.post("/api/upload")
async def upload_file_to_gcs(
    file: UploadFile = File(...),
    bucket_name: str = Form(...),
    destination_name: str = Form(""),
):
    """
    Upload a file from the browser directly to a GCS bucket.

    Accepts multipart/form-data:
      - file:             the file bytes
      - bucket_name:      target GCS bucket
      - destination_name: object name in GCS (defaults to the original filename)

    The file content is streamed in-memory — no local file path required.
    """
    import io
    try:
        from google.cloud import storage as gcs
        from google.auth import default as gcp_default

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not project_id:
            return JSONResponse({"status": "error", "message": "GOOGLE_CLOUD_PROJECT not set"}, status_code=500)
        if not creds_path or not Path(creds_path).exists():
            return JSONResponse({"status": "error", "message": "GCP credentials not found"}, status_code=500)

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        credentials, auth_project = gcp_default()
        if auth_project:
            project_id = auth_project

        client = gcs.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)

        if not bucket.exists():
            return JSONResponse(
                {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"},
                status_code=404,
            )

        object_name = destination_name.strip() or file.filename
        content_type = file.content_type or "application/octet-stream"

        file_bytes = await file.read()
        file_size = len(file_bytes)

        blob = bucket.blob(object_name)
        blob.upload_from_file(io.BytesIO(file_bytes), content_type=content_type)

        logger.info(f"Uploaded '{object_name}' ({file_size} bytes) → gs://{bucket_name}/{object_name}")

        return JSONResponse({
            "status": "success",
            "message": f"'{file.filename}' uploaded to gs://{bucket_name}/{object_name}",
            "bucket": bucket_name,
            "object": object_name,
            "size_bytes": file_size,
            "content_type": content_type,
        })

    except Exception as e:
        logger.exception("File upload error")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# WebSocket endpoint — direct browser ↔ FastAPI chat (without NestJS)
# ---------------------------------------------------------------------------
@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for direct real-time chat (fallback for the plain UI)."""
    await websocket.accept()
    user_id = "ws_user"
    logger.info(f"WebSocket connected: {session_id[:8]}…")

    await _ensure_session(session_id, user_id)

    async def send(payload: dict):
        await websocket.send_text(json.dumps(payload))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send({"type": "error", "message": "Invalid JSON"})
                continue

            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            logger.info(f"[{session_id[:8]}] User: {user_message[:80]}")
            await send({"type": "thinking", "message": "Processing…"})

            try:
                response = await asyncio.wait_for(
                    _run_agent_async(session_id, user_id, user_message),
                    timeout=180.0,
                )
            except asyncio.TimeoutError:
                response = "Request timed out after 180 seconds. Try again."

            # Cold-start retry with a fresh session
            if not response:
                retry_id = str(uuid.uuid4())
                await _ensure_session(retry_id, user_id)
                await asyncio.sleep(1)
                try:
                    response = await asyncio.wait_for(
                        _run_agent_async(retry_id, user_id, user_message),
                        timeout=180.0,
                    )
                    if response:
                        session_id = retry_id
                except asyncio.TimeoutError:
                    response = "Request timed out. Try again."

            response = response or "No response from agent."
            logger.info(f"[{session_id[:8]}] Response: {len(response)} chars")
            await send({"type": "response", "message": response, "session_id": session_id})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id[:8]}…")
    except Exception as e:
        logger.exception(f"WebSocket error [{session_id[:8]}]")
        try:
            await send({"type": "error", "message": f"Server error: {e}"})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
_ui_dir = _this_dir / "ui"
if _ui_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_ui_dir)), name="static")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "bucket_storage_agent.app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=[str(_project_root)],
    )
