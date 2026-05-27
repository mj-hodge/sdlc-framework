"""
FastAPI application entry point.

Customize:
- Add routers via app.include_router()
- Configure CORS origins for your frontend URL
- Add startup/shutdown logic in the lifespan context manager
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize resources (e.g., DB pool, cache connections)
    yield
    # Shutdown: cleanup resources


app = FastAPI(
    title="<project-name>",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # TODO: Configure for your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    # RFC 7807 Problem Details — https://datatracker.ietf.org/doc/html/rfc7807
    body: dict = {
        "type": exc.type,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": exc.instance or request.url.path,
    }
    if exc.error_code is not None:
        body["error_code"] = exc.error_code
    return JSONResponse(
        status_code=exc.status_code,
        content=body,
        media_type="application/problem+json",
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# TODO: Include routers
# from app.auth.router import router as auth_router
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
