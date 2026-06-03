"""FastAPI application factory."""
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import (
    users, skills, levels, user_skills, pipeline,
)
from src.logging_config import configure_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI app with v1 prefix."""
    configure_logging()
    app = FastAPI(title="Resource Matcher API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(users.router, prefix="/v1")
    app.include_router(skills.router, prefix="/v1")
    app.include_router(levels.router, prefix="/v1")
    app.include_router(user_skills.router, prefix="/v1")
    app.include_router(pipeline.router, prefix="/v1")

    return app
