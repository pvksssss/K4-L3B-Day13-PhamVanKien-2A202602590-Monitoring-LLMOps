from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        supplied_id = request.headers.get("x-request-id", "")
        if re.fullmatch(r"req-[0-9a-fA-F]{8}", supplied_id):
            correlation_id = supplied_id.lower()
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = max(0, int((time.perf_counter() - start) * 1000))
            if response is not None:
                response.headers["x-request-id"] = correlation_id
                response.headers["x-response-time-ms"] = str(elapsed_ms)
            clear_contextvars()
