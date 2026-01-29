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
    cd frontend && VITE_PLATFORM=desktop mise exec -- npm run tauri:dev

# Build Tauri app for production
tauri-build:
    cd frontend && VITE_PLATFORM=desktop mise exec -- npm run tauri:build

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
    cd frontend && VITE_PLATFORM=desktop VITE_BACKEND_URL=http://localhost:8090/api mise exec -- npm run tauri:dev
    wait

# Run frontend with live backend (requires LIVE_BACKEND_URL in .env)
dev-live:
    #!/usr/bin/env bash
    set -euo pipefail
    source .env
    cd frontend && VITE_PLATFORM=desktop VITE_BACKEND_URL="$LIVE_BACKEND_URL" mise exec -- npm run tauri:dev

# ============== Android ==============

# Build Android APK (ARM64)
android-build:
    cd frontend && VITE_PLATFORM=mobile mise exec -- npm run tauri android build -- --target aarch64

# Run Android app in development mode
android-dev:
    cd frontend && VITE_PLATFORM=mobile mise exec -- npm run tauri android dev

# Initialize Android project (run once)
android-init:
    cd frontend && mise exec -- npm run tauri android init

# Build and deploy Android APK to pCloud
deploy-phone: android-build
    #!/usr/bin/env bash
    set -euo pipefail
    APK_PATH="frontend/src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release-unsigned.apk"
    DEST_DIR="$HOME/pCloudDrive/android-apps/basidian"
    if [[ ! -f "$APK_PATH" ]]; then
        echo "Error: APK not found at $APK_PATH"
        exit 1
    fi
    mkdir -p "$DEST_DIR"
    cp "$APK_PATH" "$DEST_DIR/basidian.apk"
    echo "Deployed to $DEST_DIR/basidian.apk"

# ============== Utilities ==============

# Install all dependencies
deps: deps-frontend deps-backend

# Install basidian to ~/.local/bin and create desktop entry for rofi (idempotent)
install:
    #!/usr/bin/env bash
    set -euo pipefail
    BINARY="{{justfile_directory()}}/frontend/src-tauri/target/release/basidian"
    if [[ ! -f "$BINARY" ]]; then
        echo "Error: Binary not found. Run 'just tauri-build' first."
        exit 1
    fi
    mkdir -p ~/.local/bin
    ln -sf "$BINARY" ~/.local/bin/basidian
    echo "Linked basidian to ~/.local/bin/basidian"
    mkdir -p ~/.local/share/applications
    printf '%s\n' \
        "[Desktop Entry]" \
        "Name=Basidian" \
        "Comment=A second brain note-taking application" \
        "Exec=basidian" \
        "Icon=basidian" \
        "Terminal=false" \
        "Type=Application" \
        "Categories=Office;Productivity;" \
        > ~/.local/share/applications/basidian.desktop
    echo "Created ~/.local/share/applications/basidian.desktop"

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
