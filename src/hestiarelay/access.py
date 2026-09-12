"""Single fictional judge household: opaque sessions, CSRF and strict ingress."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, RedirectResponse

STATIC = Path(__file__).parent / "static"
COOKIE = "__Host-hestia"
CHALLENGE = "__Host-hestia-login"
TOKEN = re.compile(r"[A-Za-z0-9_-]{43,128}\Z")
AUTHORITY = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[1-9][0-9]{0,4})?\Z")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def valid_authority(host: str) -> bool:
    if not AUTHORITY.fullmatch(host):
        return False
    name, _, port = host.partition(":")
    return (not port or int(port) <= 65535) and all(
        part and len(part) <= 63 and not part.startswith("-") and not part.endswith("-")
        for part in name.split(".")
    )


def ingress_headers(scope):
    """Reject ambiguous authority and proxy assertions before interpreting values."""
    result = {}
    unique = {b"host", b"origin", b"cookie", b"x-csrf-token", b"content-type"}
    for key, value in scope["headers"]:
        if key in unique and key in result:
            return None
        if key.startswith(b"x-forwarded-") or key in {
            b"forwarded",
            b"x-real-ip",
            b"x-remote-user",
            b"remote-user",
        }:
            return None
        result[key] = value
    try:
        host = result.get(b"host", b"").decode("ascii")
    except UnicodeError:
        return None
    return result if valid_authority(host) else None


@dataclass(frozen=True)
class AccessConfig:
    origin: str
    key_digest: str = field(repr=False)

    @classmethod
    def from_env(cls):
        mode = os.getenv("HESTIA_ACCESS_MODE", "local")
        if mode == "local":
            return None
        if mode != "judge":
            raise ValueError("HESTIA_ACCESS_MODE must be local or judge")
        origin = os.getenv("HESTIA_PUBLIC_ORIGIN", "")
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or not valid_authority(parsed.netloc)
            or origin != "https://" + parsed.netloc
        ):
            raise ValueError("Judge mode requires one exact HTTPS origin")
        path = Path(os.getenv("HESTIA_LOGIN_KEY_FILE", ""))
        if not path.is_absolute():
            raise ValueError("Judge mode requires an absolute login key file path")
        # No key in environment variables, command arguments, logs or exception text.
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as handle:
            meta = os.fstat(handle.fileno())
            if not stat.S_ISREG(meta.st_mode) or meta.st_mode & 0o077 or meta.st_size > 129:
                raise ValueError("Login key file must be regular and owner-only")
            raw = handle.read(130).rstrip(b"\n")
        try:
            key = raw.decode("ascii")
        except UnicodeError:
            raise ValueError("Login key must be an ASCII random token") from None
        if not TOKEN.fullmatch(key):
            raise ValueError("Login key must be a random token of 43 to 128 characters")
        return cls(origin, digest(key))


@dataclass
class Session:
    csrf: str = field(repr=False)
    expires: float
    last_seen: float


class JudgeAccess:
    """One worker; restart/rotation revokes sessions but never household state."""

    def __init__(self, config: AccessConfig, clock=time.monotonic):
        self.config = config
        self.clock = clock
        self.sessions: dict[str, Session] = {}
        self.challenges: dict[str, Session] = {}
        self.attempts = deque()

    def prune(self):
        now = self.clock()
        for collection in [self.sessions, self.challenges]:
            for key, session in list(collection.items()):
                if now >= session.expires or now - session.last_seen >= 900:
                    del collection[key]
        while self.attempts and now - self.attempts[0] >= 60:
            self.attempts.popleft()

    @staticmethod
    def cookie(request, name):
        # Reject duplicate cookie names as well as duplicate Cookie header fields.
        parts = [
            part.strip().partition("=") for part in request.headers.get("cookie", "").split(";")
        ]
        values = [value for key, equal, value in parts if key == name and equal]
        return values[0] if len(values) == 1 and TOKEN.fullmatch(values[0]) else ""

    @staticmethod
    def set_cookie(response, name, token, seconds):
        response.set_cookie(
            name, token, max_age=seconds, secure=True, httponly=True, samesite="strict", path="/"
        )

    @staticmethod
    def csrf_matches(request, session):
        supplied = request.headers.get("x-csrf-token", "")
        return bool(
            session and TOKEN.fullmatch(supplied) and secrets.compare_digest(supplied, session.csrf)
        )

    async def response(self, scope, receive):
        """Return a response or None only for an authorized application request."""
        self.prune()
        request = Request(scope, receive)
        path, method = scope["path"], scope["method"]
        if scope.get("scheme") != "https":
            return JSONResponse({"error": "HTTPS required"}, status_code=403)
        if scope.get("query_string"):
            return JSONResponse({"error": "Query parameters are not accepted"}, status_code=400)
        if request.headers.get("host") != self.config.origin[8:]:
            return JSONResponse({"error": "Host or Origin not allowed"}, status_code=403)
        origin = request.headers.get("origin")
        if (origin is not None and origin != self.config.origin) or (
            method not in {"GET", "HEAD"} and origin != self.config.origin
        ):
            return JSONResponse({"error": "Host or Origin not allowed"}, status_code=403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"error": "Same-origin access required"}, status_code=403)
        if path == "/mcp" or path.startswith("/mcp/"):
            return JSONResponse({"error": "Remote MCP is not enabled"}, status_code=404)
        if path == "/health" and method == "GET":
            return JSONResponse({"status": "ok", "service": "hestiarelay"})
        token = self.cookie(request, COOKIE)
        session = self.sessions.get(digest(token))
        if path == "/auth/session" and method == "GET":
            if session:
                return JSONResponse(
                    {"required": True, "authenticated": True, "csrf_token": session.csrf}
                )
            # Pre-login CSRF token bound to an HttpOnly cookie, never a URL.
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            if len(self.challenges) >= 128:
                self.challenges.pop(next(iter(self.challenges)))
            self.challenges[digest(token)] = Session(csrf, self.clock() + 300, self.clock())
            response = JSONResponse({"required": True, "authenticated": False, "csrf_token": csrf})
            self.set_cookie(response, CHALLENGE, token, 300)
            return response
        if path == "/auth/login" and method == "POST":
            return await self.login(request, token)
        if path == "/auth/logout" and method == "POST":
            if not session:
                return JSONResponse({"error": "Sign in required"}, status_code=401)
            if not self.csrf_matches(request, session):
                return JSONResponse({"error": "Invalid request token"}, status_code=403)
            self.sessions.pop(digest(token))
            response = JSONResponse({"signed_out": True})
            self.set_cookie(response, COOKIE, "", 0)
            return response
        if path.startswith("/auth/"):
            return JSONResponse({"error": "Unknown access operation"}, status_code=404)
        if path == "/login" and method == "GET":
            return (
                RedirectResponse("/", status_code=303)
                if session
                else FileResponse(STATIC / "login.html")
            )
        if path in {"/static/login.js", "/static/style.css", "/static/mark.svg"} and method in {
            "GET",
            "HEAD",
        }:
            return FileResponse(STATIC / path.rsplit("/", 1)[1])
        if not session:
            if path == "/" and method == "GET":
                return RedirectResponse("/login", status_code=303)
            return JSONResponse({"error": "Sign in required"}, status_code=401)
        if method not in {"GET", "HEAD"} and not self.csrf_matches(request, session):
            return JSONResponse({"error": "Invalid request token"}, status_code=403)
        session.last_seen = self.clock()
        return None

    async def login(self, request, old_token):
        if len(self.attempts) >= 20:
            return JSONResponse(
                {"error": "Please wait a minute before trying again"},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        self.attempts.append(self.clock())
        challenge_key = digest(self.cookie(request, CHALLENGE))
        if not self.csrf_matches(request, self.challenges.get(challenge_key)):
            return JSONResponse(
                {"error": "Refresh the sign-in page and try again"}, status_code=403
            )
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return JSONResponse({"error": "JSON required"}, status_code=415)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 1024:
                return JSONResponse({"error": "Request too large"}, status_code=413)
        try:
            data = json.loads(body)
            valid = isinstance(data, dict) and set(data) == {"key"}
            key = data.get("key") if valid else None
            valid = isinstance(key, str) and TOKEN.fullmatch(key)
        except (ValueError, UnicodeError):
            valid, key = False, None
        if not valid or not secrets.compare_digest(digest(key), self.config.key_digest):
            return JSONResponse(
                {"error": "Sign-in unsuccessful. Check your access key."}, status_code=401
            )
        if self.challenges.pop(challenge_key, None) is None:
            return JSONResponse({"error": "Sign-in request already used"}, status_code=403)
        self.sessions.pop(digest(old_token), None)
        if len(self.sessions) >= 64:
            self.sessions.pop(next(iter(self.sessions)))
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        self.sessions[digest(token)] = Session(csrf, self.clock() + 3600, self.clock())
        response = JSONResponse({"authenticated": True, "csrf_token": csrf})
        self.set_cookie(response, COOKIE, token, 3600)
        self.set_cookie(response, CHALLENGE, "", 0)
        return response
