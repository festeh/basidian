# Justfile for Basidian - Second Brain App

# Default recipe: show available commands
default:
    @just --list

# ============== Backend ==============

# Run backend server
backend:
    cd backend && uv run basidian-server serve --http=0.0.0.0:8090

# Run backend with hot reload
backend-dev:
    cd backend && uv run uvicorn basidian_server.main:create_app --factory --reload --host 0.0.0.0 --port 8090

# Install backend dependencies
deps-backend:
    cd backend && uv sync

# ============== Frontend (Tauri) ==============

# Run Tauri app in development mode
tauri-dev:
    cd frontend && npm run tauri:dev

# Build Tauri app for production
tauri-build:
    cd frontend && npm run tauri:build

# Install frontend dependencies
deps-frontend:
    cd frontend && npm install

# Type check frontend
check:
    cd frontend && npm run check

# ============== Local Development ==============

# Run backend + frontend locally
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && uv run basidian-server serve --http=0.0.0.0:8090) &
    sleep 2
    cd frontend && VITE_BACKEND_URL=http://localhost:8090/api npm run tauri:dev
    wait

# ============== Utilities ==============

# Install all dependencies
deps: deps-frontend deps-backend

# Clean all build artifacts
clean:
    rm -rf frontend/build frontend/src-tauri/target
    rm -rf backend/.venv backend/dist backend/build

# Format code
fmt:
    cd frontend && npx prettier --write .

# Lint code
lint:
    cd frontend && npm run check
