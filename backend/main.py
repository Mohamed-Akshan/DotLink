from typing import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from core.config import settings
from core.logger import setup_logging
from database.connection import Base, engine
from database import models
from routes import (
    auth,
    overview,
    clients,
    projects,
    services,
    finance,
    approvals,
    settings as settings_routes,
    chat, expenses,
)

logger = setup_logging()


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    """Initialize application tables."""

    if len(settings.secret_key) < 32:

        raise RuntimeError("Set SECRET_KEY to at least 32 characters in .env")

    Base.metadata.create_all(engine)
    from database.migrate import upgrade
    upgrade(engine)
    yield


app = FastAPI(title="DotLink API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in [auth, overview, clients, projects, services, finance, approvals, settings_routes, chat, expenses]:

    app.include_router(module.router)


@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_error(request: Request, error) -> JSONResponse:
    """Return readable validation errors without echoing passwords or input."""

    messages = []

    for item in error.errors():

        location = item.get("loc", ())
        field = str(location[-1]).replace("_", " ") if location else "Details"
        messages.append(f"{field.capitalize()}: {item['msg']}")

    return JSONResponse(status_code=422, content={"detail": "; ".join(messages)})


@app.get("/health")
def health() -> dict:
    """Return a simple application health check."""

    return {"status": "ok"}
