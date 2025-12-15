# Justfile for Rumi - Daily Notes App
# Root-level commands for managing frontend and backend

# Default recipe: show available commands
default:
    @just --list

# ============== Backend (Go/PocketBase) ==============

# Build the backend server
build-backend:
    cd backend && go build -o rumi-server .

# Run the backend server
run-backend:
    cd backend && ./rumi-server serve

# Run backend with auto-rebuild on changes (requires air)
dev-backend:
    cd backend && go run . serve

# Clean backend build artifacts
clean-backend:
    rm -f backend/rumi-server

# ============== Frontend (Flutter) ==============

# Run frontend on Linux
run-linux:
    cd frontend && just run-linux

# Run frontend on Android
run-android:
    cd frontend && just run-android

# Build Linux release
build-linux:
    cd frontend && just build-linux

# Build Android APK
build-android-apk:
    cd frontend && just build-android-apk

# Build Android App Bundle
build-android-aab:
    cd frontend && just build-android-aab

# Install frontend dependencies
deps-frontend:
    cd frontend && flutter pub get

# Clean frontend build artifacts
clean-frontend:
    cd frontend && flutter clean

# Run frontend tests
test-frontend:
    cd frontend && flutter test

# Format frontend code
format-frontend:
    cd frontend && dart format .

# Analyze frontend code
analyze-frontend:
    cd frontend && flutter analyze

# ============== Combined Commands ==============

# Run both backend and frontend (Linux) in parallel
run-all-linux:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && ./rumi-server serve) &
    sleep 2
    (cd frontend && just run-linux) &
    wait

# Run both backend and frontend (Android) in parallel
run-all-android:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && ./rumi-server serve) &
    sleep 2
    (cd frontend && just run-android) &
    wait

# Development mode: run backend and frontend together (Linux) - uses .env URLs
dev-linux:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && go run . serve) &
    sleep 2
    (cd frontend && just run-linux) &
    wait

# Development mode: run backend and frontend together (Android) - uses .env URLs
dev-android:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && go run . serve) &
    sleep 2
    (cd frontend && just run-android) &
    wait

# Local development: run local backend and frontend (Linux) pointing to localhost
dev-local-linux:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && go run . serve --http=0.0.0.0:8090) &
    sleep 2
    cd frontend && flutter run -d linux --dart-define=BACKEND_URL=http://localhost:8090/api --dart-define=TRANSCRIPTION_URL=http://localhost:8091 &
    wait

# Local development: run local backend and frontend (Android) pointing to host machine
dev-local-android:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && go run . serve --http=0.0.0.0:8090) &
    sleep 2
    # Android emulator uses 10.0.2.2 to reach host machine
    cd frontend && flutter run -d $(flutter devices | grep android | head -1 | awk -F'•' '{print $2}' | xargs) --dart-define=BACKEND_URL=http://10.0.2.2:8090/api --dart-define=TRANSCRIPTION_URL=http://10.0.2.2:8091 &
    wait

# Install all dependencies
deps: deps-frontend
    cd backend && go mod download

# Clean all build artifacts
clean: clean-frontend clean-backend

# Build everything
build: build-backend build-linux

# Show Flutter devices
devices:
    flutter devices

# Show Flutter doctor info
doctor:
    flutter doctor
