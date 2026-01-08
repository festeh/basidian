# Basidian Frontend

A second brain note-taking app built with Tauri v2 + Svelte 5.

## Stack

- **Frontend**: Svelte 5 + SvelteKit + TypeScript
- **Desktop**: Tauri v2 (Rust)
- **Tooling**: Vite, mise (Rust + Node)

## Prerequisites

Install system dependencies (Arch Linux):

```bash
sudo pacman -S webkit2gtk-4.1 libappindicator-gtk3
```

## Development

```bash
# Install dependencies
npm install

# Run Tauri app in dev mode
npm run tauri:dev
```

Or from root directory:

```bash
just dev  # Starts backend + frontend
```

## Building

```bash
npm run tauri:build
```

Output will be in `src-tauri/target/release/bundle/`.
