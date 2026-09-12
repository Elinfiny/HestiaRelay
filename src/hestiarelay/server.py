from __future__ import annotations

import json

import uvicorn
from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hestiarelay.bedrock import BedrockPlanner
from hestiarelay.engine import HouseholdEngine
from hestiarelay.service import HouseholdService
from hestiarelay.store import SQLiteStateStore
from hestiarelay.web import LocalBoundary, register_web

mcp = MCPServer(
    "HestiaRelay",
    instructions=(
        "Persistent household continuity agent. Use bounded household planning tools, preserve "
        "context across sessions, and never bypass consent gates for sensitive proposals."
    ),
)
engine = HouseholdEngine(SQLiteStateStore())
planner = BedrockPlanner()
service = HouseholdService(engine, planner)


@mcp.tool()
def start_household_goal(
    title: str,
    when: str,
    people: int,
    budget_usd: float | None = None,
) -> str:
    """Start or replace the active household goal and persist it across MCP sessions."""
    state = engine.start_goal(
        title=title,
        when=when,
        people=people,
        budget_usd=budget_usd,
    )
    return state.model_dump_json(indent=2)


@mcp.tool()
def remember_household_preference(person: str, note: str) -> str:
    """Persist a household preference or constraint for later sessions."""
    state = engine.remember_preference(person=person, note=note)
    return state.model_dump_json(indent=2)


@mcp.tool()
def get_continuity_brief() -> str:
    """Return the current cross-session household goal, preferences, and approval count."""
    return engine.continuity_brief()


@mcp.tool()
def generate_household_plan() -> str:
    """Generate a bounded plan with Amazon Bedrock when configured, otherwise deterministic."""
    result = service.generate_plan()
    return result.model_dump_json(indent=2)


@mcp.tool()
def propose_household_action(kind: str, description: str, payload_json: str = "{}") -> str:
    """Create a risk-classified action proposal; sensitive proposals require confirmation."""
    payload = json.loads(payload_json)
    if not isinstance(payload, dict):
        raise ValueError("payload_json must encode a JSON object")
    proposal = engine.propose_action(kind=kind, description=description, payload=payload)
    return proposal.model_dump_json(indent=2)


@mcp.tool()
def decide_sensitive_action(action_id: str, approved: bool) -> str:
    """Approve or reject exactly one pending proposal without executing an external side effect."""
    proposal = engine.decide_proposal(action_id=action_id, approved=approved)
    return proposal.model_dump_json(indent=2)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> Response:
    return JSONResponse(
        {
            "status": "ok",
            "service": "hestiarelay",
            "transport": "streamable-http",
            "mcp_minimum_target": "2025-11-25",
            "bedrock_configured": planner.configured,
        }
    )


@mcp.tool()
def start_simulator_session(session_id: str) -> dict:
    """Open a distinct simulated session; recover, never reset, household context."""
    from uuid import UUID

    return service.new_session(str(UUID(session_id)))


@mcp.tool()
def send_simulator_message(session_id: str, request_id: str, text: str) -> dict:
    """Exercise the same guided three-session service as the browser UI."""
    from hestiarelay.web import MessageInput

    data = MessageInput(session_id=session_id, request_id=request_id, text=text)
    return service.message(**data.model_dump(mode="json"))


register_web(mcp, service)
app = LocalBoundary(mcp.streamable_http_app(json_response=True))


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
