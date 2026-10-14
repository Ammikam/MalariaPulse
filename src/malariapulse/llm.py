"""Gemini tool-calling loop over MCP tools (used by --mode llm).

The model sees the MCP tools of ONE agent (its allowed servers) as function declarations,
decides which to call and in what order, and we execute each call through the MCP ToolHub.
Swap this file to use a different / open-source model: only `run_agent` must keep its signature.

NOTE: this path needs GEMINI_API_KEY and has not been exercised against the live API in the
scaffold; the rules mode is the tested path. Test llm mode first thing and fix any SDK drift.
"""
import json
import os

from .mcp_client import ToolHub

MAX_STEPS = 12


def _declarations(hub: ToolHub, servers: list[str]):
    from google.genai import types

    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=name,
                    description=meta["description"],
                    parameters_json_schema=meta["schema"],
                )
                for name, meta in hub.tools_for(servers).items()
            ]
        )
    ]


async def run_agent(hub: ToolHub, system_prompt: str, task: str, servers: list[str]) -> tuple[str, list[dict]]:
    """Run one agent. Returns (final_text, trace) where trace lists every tool call made."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env, or use --mode rules.")
    client = genai.Client(api_key=api_key)
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=_declarations(hub, servers),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=task)])]
    trace: list[dict] = []

    for _ in range(MAX_STEPS):
        response = await client.aio.models.generate_content(model=model, contents=contents, config=config)
        calls = response.function_calls or []
        if not calls:
            return (response.text or "").strip(), trace
        contents.append(response.candidates[0].content)
        parts = []
        for call in calls:
            args = dict(call.args or {})
            try:
                result = await hub.call(call.name, **args)
            except Exception as exc:  # report errors back to the model so it can recover
                result = {"error": str(exc)}
            trace.append({"tool": call.name, "args": args})
            parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))
        contents.append(types.Content(role="user", parts=parts))
    return "Stopped: too many tool-call steps.", trace


def parse_json(text: str):
    """Extract a JSON object/array from model output (handles ```json fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[4:] if text.lower().startswith("json") else text
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=-1)
    if start == -1:
        raise ValueError("No JSON found in model output")
    return json.loads(text[start:])
