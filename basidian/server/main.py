import json
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import click
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .db import close_db, init_db
from .handlers import filesystem_router, notes_router

# Configure loguru - stderr output
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# Configure loguru - JSON file output
LOG_DIR = Path(tempfile.gettempdir()) / "basidian"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "backend.log"


def json_sink(message):
    record = message.record
    entry = {
        "ts": record["time"].isoformat(),
        "level": record["level"].name.lower(),
        "module": record["name"],
        "msg": record["message"],
    }
    if record["extra"]:
        entry["data"] = record["extra"]
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


logger.add(json_sink, level="DEBUG")


def create_app(db_path: str = "data/basidian.db") -> FastAPI:
    """Create the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db(app, db_path)
        logger.info(f"Database initialized: {db_path}")
        yield
        await close_db(app)
        logger.info("Database connection closed")

    app = FastAPI(title="Basidian Backend", lifespan=lifespan)

    # CORS - allow all origins
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

    return app


@click.group()
def cli():
    """Basidian backend server."""
    pass


@cli.command()
@click.option("--http", default=":8090", help="HTTP server address (e.g., :8090 or 0.0.0.0:8090)")
@click.option("--db", "db_path", default="data/basidian.db", help="SQLite database path")
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
    logger.info(f"Logs: {LOG_FILE}")
    app = create_app(db_path)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli()
