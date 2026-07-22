"""Real MCP client agent for the SENTRY demo.

    AI Agent --MCP--> [SENTRY checkpoint: POST /execute] --MCP--> Tool Server

Every proposed tool call is first sent to the live SENTRY API (the actual FastAPI
service in src/, not a local function) for a decision. Only ALLOW decisions ever
reach the real MCP call_tool() against mcp_demo/tools_server.py.

Requires the SENTRY API to be running (see README: `docker-compose up` or
`uvicorn src.main:app --reload`).
"""

import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SENTRY_API_URL = os.getenv("SENTRY_API_URL", "http://localhost:8000")
SERVER_PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "mcp_demo.tools_server"])


@dataclass
class ExecutionResult:
    request: dict[str, Any]
    response: dict[str, Any]
    tool_result: dict[str, Any] | None


class SentryMCPAgent:
    def __init__(self, session: ClientSession, http_client: httpx.AsyncClient) -> None:
        self._session = session
        self._http = http_client

    @classmethod
    def connect(cls, http_client: httpx.AsyncClient) -> "_AgentContext":
        """Usage: `async with SentryMCPAgent.connect(http_client) as agent:`"""
        return _AgentContext(http_client)

    async def propose(self, tool: str, parameters: dict[str, Any], **execution_fields) -> ExecutionResult:
        request = {"tool_name": tool, "parameters": parameters, **execution_fields}

        response = await self._http.post(f"{SENTRY_API_URL}/execute", json=request)
        response.raise_for_status()
        decision = response.json()

        tool_result = None
        if decision["decision"] == "ALLOW":
            mcp_result = await self._session.call_tool(tool, arguments=parameters)
            tool_result = _content_to_dict(mcp_result)

        return ExecutionResult(request=request, response=decision, tool_result=tool_result)


class _AgentContext:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def __aenter__(self) -> SentryMCPAgent:
        self._stdio_cm = stdio_client(SERVER_PARAMS)
        read, write = await self._stdio_cm.__aenter__()
        self._session_cm = ClientSession(read, write)
        session = await self._session_cm.__aenter__()
        await session.initialize()
        return SentryMCPAgent(session, self._http)

    async def __aexit__(self, *exc_info) -> None:
        await self._session_cm.__aexit__(*exc_info)
        await self._stdio_cm.__aexit__(*exc_info)


def _content_to_dict(mcp_result) -> dict:
    import json

    block = mcp_result.content[0]
    text = getattr(block, "text", str(block))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}
