"""
GCS Storage Agent — MCP Server

Exposes the GCS Storage Agent as an MCP (Model Context Protocol) server so that
external coding agents (Claude Code, Cursor, Windsurf, etc.) can invoke storage
operations and website deployment directly as native tools.

Usage — start the server:
    python bucket_storage_agent/mcp_server.py

Claude Code configuration (~/.claude/mcp.json or project .mcp.json):
    {
      "mcpServers": {
        "gcs-storage-agent": {
          "command": "python",
          "args": ["bucket_storage_agent/mcp_server.py"],
          "cwd": "/path/to/GCP-Cloudmate-ai"
        }
      }
    }

Cursor / Windsurf — add the same block to their MCP settings UI.

Requires FastAPI backend running at AGENT_URL (default: http://localhost:8080).
"""

import os
import sys
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AGENT_URL = os.getenv("AGENT_API_URL", "http://localhost:8080")
TIMEOUT   = 180.0   # seconds — complex agent ops can take a while

mcp = FastMCP(
    name="gcs-storage-agent",
    instructions=(
        "Tools for managing Google Cloud Storage via the GCS Storage Agent. "
        "Use `deploy_website` after building HTML/CSS/JS to publish to a GCS bucket. "
        "Use `gcs_command` for any other storage operation (buckets, IAM, cost, lifecycle, etc.)."
    ),
)


# ---------------------------------------------------------------------------
# Tool: deploy_website
# Designed for coding agents that build websites and want to deploy them.
# ---------------------------------------------------------------------------
@mcp.tool()
async def deploy_website(
    bucket_name: str,
    index_html: str,
    html_404: str = "",
) -> str:
    """
    Deploy a website to a Google Cloud Storage bucket.

    Call this after building a website to upload the HTML files and make them
    publicly accessible via GCS static website hosting.

    Args:
        bucket_name: The GCS bucket name to deploy to (must already have website
                     hosting enabled, or ask the agent to enable it first).
        index_html:  Full HTML content of the main page (index.html).
        html_404:    Full HTML content of the 404 error page (optional).

    Returns:
        Agent response describing what was uploaded and the public URLs.
    """
    files = [{"filename": "index.html", "content": index_html}]
    if html_404:
        files.append({"filename": "404.html", "content": html_404})

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{AGENT_URL}/api/deploy",
            json={"bucket_name": bucket_name, "files": files},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "Deployment complete.")


# ---------------------------------------------------------------------------
# Tool: enable_website_hosting
# Convenience wrapper — enable hosting before deploying.
# ---------------------------------------------------------------------------
@mcp.tool()
async def enable_website_hosting(bucket_name: str) -> str:
    """
    Enable static website hosting on a GCS bucket.

    Configures the bucket for public web access, sets IAM to allow public reads,
    and configures CORS. Call this before deploy_website if hosting isn't enabled.

    Args:
        bucket_name: The GCS bucket to configure for website hosting.

    Returns:
        Agent response with the website URL and configuration details.
    """
    message = (
        f"Enable static website hosting on bucket '{bucket_name}' with index.html "
        f"as the main page and 404.html as the error page. Configure public access and CORS."
    )
    return await _chat(message)


# ---------------------------------------------------------------------------
# Tool: gcs_command
# General-purpose passthrough for any natural language GCS operation.
# ---------------------------------------------------------------------------
@mcp.tool()
async def gcs_command(instruction: str) -> str:
    """
    Send any natural language instruction to the GCS Storage Agent.

    Use this for any storage operation not covered by the dedicated tools:
    creating/deleting buckets, managing objects, setting lifecycle rules,
    IAM policies, cost analysis, backups, migrations, etc.

    Examples:
        "Create a bucket called my-website-bucket in US region"
        "List all buckets in my project"
        "Enable versioning on my-data-bucket"
        "Set lifecycle rules to archive objects older than 30 days"
        "Show cost estimates for all my buckets"
        "Audit security and IAM policies"

    Args:
        instruction: Natural language instruction for the GCS agent.

    Returns:
        Agent response with results and any relevant details.
    """
    return await _chat(instruction)


# ---------------------------------------------------------------------------
# Shared HTTP helper
# ---------------------------------------------------------------------------
async def _chat(message: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{AGENT_URL}/api/chat",
            json={"message": message},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "No response from agent.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
