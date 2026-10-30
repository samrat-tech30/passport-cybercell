"""FastAPI app: wiring only (config, database, middleware, error format, routes).

Run:  uvicorn app.main:app --reload --port 8000      (from the backend/ folder)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.gateway_routes import router as gateway_router
from app.api.routes import router
from app.config import get_settings
from app.db import database
from app.gate.policy import load_policy
from app.scenarios import load_scenarios
from app.security import BodySizeLimitMiddleware, SecurityHeadersMiddleware

log = logging.getLogger("passport")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database.connect(settings.db_path)
    load_policy()  # a broken policy stops start-up: fail closed
    load_scenarios()
    log.info(
        "PASSPORT %s started: env=%s live_llm=%s access_code=%s origins=%s",
        __version__,
        settings.app_env,
        settings.live_llm_ready,
        settings.demo_access_code is not None,
        ",".join(settings.allowed_origins),
    )
    yield
    database.close()


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = FastAPI(
        title="PASSPORT API",
        version=__version__,
        lifespan=lifespan,
        docs_url=None if settings.app_env == "prod" else "/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Demo-Code"],
        max_age=600,
    )
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        detail = (
            exc.detail if isinstance(exc.detail, dict) else {"code": "http_error", "message": str(exc.detail)}
        )
        return JSONResponse(
            {"error": detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = f"{where}: {first.get('msg', 'invalid input')}" if where else first.get("msg", "invalid input")
        return JSONResponse({"error": {"code": "invalid_input", "message": msg}}, status_code=422)

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error")
        return JSONResponse(
            {"error": {"code": "internal_error", "message": "Something went wrong on our side."}},
            status_code=500,
        )

    app.include_router(router)
    app.include_router(gateway_router)
    return app


app = create_app()
