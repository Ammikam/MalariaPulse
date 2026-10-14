"""MCP client hub: starts every MCP server over stdio and exposes their tools to the agents."""
import json
import os
import sys
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVERS = {
    "clinical": "malariapulse.mcp_servers.clinical_server",
    "environment": "malariapulse.mcp_servers.environment_server",
    "forecast": "malariapulse.mcp_servers.forecast_server",
    "supply": "malariapulse.mcp_servers.supply_server",
    "outreach": "malariapulse.mcp_servers.outreach_server",
}


class ToolHub:
    """Async context manager that connects to all MCP servers and routes tool calls."""

    def __init__(self, servers: dict[str, str] | None = None):
        self.servers = servers or SERVERS
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}   # tool name -> session
        self.tools: dict[str, dict] = {}                # tool name -> {server, description, schema}
        self.calls: list[dict] = []                     # audit log of every tool call
        self.current_agent = ""                          # label recorded in the audit log

    @staticmethod
    def _child_env() -> dict[str, str]:
        """Environment for the server subprocesses (the MCP SDK only forwards a minimal env by default)."""
        src_dir = str(Path(__file__).resolve().parents[1])
        env = {"PYTHONPATH": os.pathsep.join(filter(None, [src_dir, os.environ.get("PYTHONPATH", "")]))}
        env["FASTMCP_LOG_LEVEL"] = os.environ.get("FASTMCP_LOG_LEVEL", "WARNING")
        for key in ("MALARIAPULSE_DATA", "MALARIAPULSE_DB"):
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    async def __aenter__(self):
        for server_name, module in self.servers.items():
            params = StdioServerParameters(command=sys.executable, args=["-m", module], env=self._child_env())
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            for tool in (await session.list_tools()).tools:
                self._sessions[tool.name] = session
                self.tools[tool.name] = {
                    "server": server_name,
                    "description": tool.description or "",
                    "schema": tool.inputSchema,
                }
        return self

    async def __aexit__(self, *exc):
        await self._stack.aclose()

    async def call(self, name: str, **arguments):
        """Call an MCP tool and return its result as plain Python data."""
        if name not in self._sessions:
            raise KeyError(f"Unknown MCP tool: {name}")
        self.calls.append({"agent": self.current_agent, "tool": name, "args": arguments})
        result = await self._sessions[name].call_tool(name, arguments)
        if result.isError:
            text = " ".join(getattr(c, "text", "") for c in result.content)
            raise RuntimeError(f"Tool {name} failed: {text}")
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return structured.get("result", structured) if isinstance(structured, dict) else structured
        texts = [c.text for c in result.content if getattr(c, "text", None)]
        parsed = []
        for t in texts:
            try:
                parsed.append(json.loads(t))
            except json.JSONDecodeError:
                parsed.append(t)
        return parsed[0] if len(parsed) == 1 else parsed

    def tools_for(self, servers: list[str]) -> dict[str, dict]:
        return {n: t for n, t in self.tools.items() if t["server"] in servers}
