"""Small same-origin simulator API; no external side-effect adapter."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from hestiarelay.access import ingress_headers
from hestiarelay.service import HouseholdService

STATIC = Path(__file__).parent / "static"


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID


class MessageInput(SessionInput):
    request_id: UUID
    text: str = Field(min_length=1, max_length=500)


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: UUID
    approved: StrictBool


def register_web(mcp, service: HouseholdService):
    @mcp.custom_route("/", methods=["GET"])
    async def index(request: Request):
        return FileResponse(STATIC / "index.html")

    @mcp.custom_route("/static/{name}", methods=["GET"])
    async def asset(request: Request):
        name = request.path_params["name"]
        if name not in {"app.js", "style.css", "mark.svg"}:
            return JSONResponse({"error": "Unknown asset"}, status_code=404)
        return FileResponse(STATIC / name)

    @mcp.custom_route("/api/state", methods=["GET"])
    async def state(request: Request):
        return JSONResponse(await run_in_threadpool(service.snapshot))

    async def command(request: Request, schema, handler):
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return JSONResponse({"error": "JSON required"}, status_code=415)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 4096:
                return JSONResponse({"error": "Request too large"}, status_code=413)
        try:
            data = schema.model_validate_json(body).model_dump(mode="json")
            return JSONResponse(await run_in_threadpool(handler, **data))
        except ValidationError:
            return JSONResponse({"error": "Invalid input fields."}, status_code=422)
        except KeyError:
            return JSONResponse({"error": "Session or proposal not found."}, status_code=404)
        except ValueError as error:
            return JSONResponse({"error": str(error)}, status_code=409)

    @mcp.custom_route("/api/session", methods=["POST"])
    async def session(request: Request):
        return await command(request, SessionInput, service.new_session)

    @mcp.custom_route("/api/message", methods=["POST"])
    async def message(request: Request):
        return await command(request, MessageInput, service.message)

    @mcp.custom_route("/api/decision", methods=["POST"])
    async def decision(request: Request):
        return await command(request, DecisionInput, service.decide)


class LocalBoundary:
    """Protect custom routes as well as MCP. Public deployment is a later gate."""

    def __init__(self, app, access=None):
        self.app = app
        self.access = access

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            return await send({"type": "websocket.close", "code": 1008})
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = ingress_headers(scope)

        async def secured_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (
                        b"content-security-policy",
                        (
                            b"default-src 'self'; script-src 'self'; style-src 'self'; "
                            b"img-src 'self'; connect-src 'self'; frame-ancestors 'self'; "
                            b"base-uri 'none'; form-action 'self'"
                        ),
                    ),
                ]
            await send(message)

        try:
            if headers is None:
                response = JSONResponse({"error": "Invalid request authority"}, status_code=403)
            elif self.access:
                response = await self.access.response(scope, receive)
            else:
                host = headers[b"host"].decode("ascii")
                origin = headers.get(b"origin")
                allowed = {f"http://{host}".encode(), f"https://{host}".encode()}
                if host.split(":")[0] not in {"127.0.0.1", "localhost"} or (
                    origin is not None and origin not in allowed
                ):
                    response = JSONResponse(
                        {"error": "Host or Origin not allowed"}, status_code=403
                    )
                elif scope["path"] == "/auth/session" and scope["method"] == "GET":
                    response = JSONResponse({"required": False, "authenticated": False})
                else:
                    response = None
            if response is not None:
                return await response(scope, receive, secured_send)
            await self.app(scope, receive, secured_send)
        except (OSError, json.JSONDecodeError):
            response = JSONResponse(
                {"error": "State unavailable; no completion claimed."}, status_code=503
            )
            await response(scope, receive, secured_send)
