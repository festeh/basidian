# Justfile for Basidian - Second Brain App

# Default recipe: show available commands
default:
    @just --list

# ============== Backend ==============

# Run backend server
backend:
    cd backend && uv run basidian-server serve

# Run backend with hot reload
backend-dev:
    cd backend && uv run uvicorn basidian_server.main:create_app --factory --reload --host 0.0.0.0 --port 8090

# Install backend dependencies
deps-backend:
    cd backend && uv sync

# ============== Frontend ==============

# Run frontend on Linux (uses .env for remote backend)
run:
    cd frontend && just run-linux

# Run frontend on Android (uses .env for remote backend)
run-android:
    cd frontend && just run-android

# Run frontend on Linux pointing to local backend
run-local:
    cd frontend && flutter run -d linux \
        --dart-define=BACKEND_URL=http://localhost:8090/api \
        --dart-define=TRANSCRIPTION_URL=http://localhost:8091

# Build Linux release
build-linux:
    cd frontend && just build-linux

# Build Android APK
build-android:
    cd frontend && just build-android-apk

# Install frontend dependencies
deps-frontend:
    cd frontend && flutter pub get

# ============== Local Development ==============

# Run backend + frontend locally (Linux)
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && uv run basidian-server serve --http=0.0.0.0:8090) &
    sleep 2
    cd frontend && flutter run -d linux \
        --dart-define=BACKEND_URL=http://localhost:8090/api \
        --dart-define=TRANSCRIPTION_URL=http://localhost:8091
    wait

# Run backend + frontend locally (Android emulator)
dev-android:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && uv run basidian-server serve --http=0.0.0.0:8090) &
    sleep 2
    cd frontend && flutter run \
        --dart-define=BACKEND_URL=http://10.0.2.2:8090/api \
        --dart-define=TRANSCRIPTION_URL=http://10.0.2.2:8091
    wait

# ============== Utilities ==============

# Install all dependencies
deps: deps-frontend deps-backend

# Clean all build artifacts
clean:
    cd frontend && flutter clean
    rm -rf backend/.venv backend/dist backend/build

# Run frontend tests
test:
    cd frontend && flutter test

# Format code
fmt:
    cd frontend && dart format .

# Analyze code
lint:
    cd frontend && flutter analyze

# Show Flutter devices
devices:
    flutter devices
