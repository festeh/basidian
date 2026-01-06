import logging
from contextlib import asynccontextmanager

import click
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import database as db
from .handlers import daily_router, filesystem_router, notes_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
