import sys
import time
from contextlib import asynccontextmanager

import click
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from . import database as db
from .handlers import daily_router, filesystem_router, notes_router

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)


def create_app(db_path: str = "./pb_data/data.db") -> FastAPI:
    """Create the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: Initialize database
        await db.init(db_path)
        logger.info(f"Database initialized: {db_path}")
        yield
        # Shutdown: Close database
        await db.close()
        logger.info("Database connection closed")

    app = FastAPI(title="Basidian Backend", lifespan=lifespan)

    # CORS - allow all origins (same as Go)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.1f}ms)"
        )
        return response

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "basidian-backend"}

    # Include routers
    app.include_router(notes_router)
    app.include_router(filesystem_router)
    app.include_router(daily_router)

    return app


@click.group()
def cli():
    """Basidian backend server."""
    pass


@cli.command()
@click.option("--http", default=":8090", help="HTTP server address (e.g., :8090 or 0.0.0.0:8090)")
@click.option("--db", "db_path", default="./pb_data/data.db", help="SQLite database path")
def serve(http: str, db_path: str):
    """Start the Basidian backend server."""
    # Parse host:port from --http flag
    if http.startswith(":"):
        host = "0.0.0.0"
        port = int(http[1:])
    else:
        parts = http.split(":")
        host = parts[0] if parts[0] else "0.0.0.0"
        port = int(parts[1]) if len(parts) > 1 else 8090

    logger.info(f"Server starting on {host}:{port}")
    app = create_app(db_path)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli()
