# Frontend UI

## Overview

The frontend is a SvelteKit application using Svelte 5 runes, built as a static site and served inside a Tauri shell for desktop and mobile. It provides a markdown editor with a file tree, theming, and plugin-driven UI slots.

## How It Works

### Layout

```
Desktop:
┌──────────────────────────────────────────┐
│ TopBarDesktop (drag zone, window ctrls)  │
├──────────┬───────────────────────────────┤
│ Sidebar  │ Editor                        │
│ (search, │ (CodeMirror / MarkdownPreview)│
│  tree,   │                               │
│  plugin  │                               │
│  actions)│                               │
├──────────┴───────────────────────────────┤
│ StatusBar (plugin slots)                 │
└──────────────────────────────────────────┘

Mobile:
┌──────────────────────┐
│ TopBarMobile (burger) │
├──────────────────────┤
│ Editor (full width)  │
│                      │
│  Sidebar overlays    │
│  when opened         │
└──────────────────────┘
```

### Editor

CodeMirror 6 with:
- Markdown syntax highlighting
- Optional Vim keybindings (setting)
- Auto-save with 2.5-second debounce
- Toggle between edit and preview modes

Preview uses markdown-it with Shiki for syntax highlighting and KaTeX for math.

### Theming

Five built-in themes defined as CSS variable maps:
- Catppuccin Mocha, Catppuccin Latte, Nord, Dracula, Gruvbox Dark

`applyTheme()` writes CSS variables to `:root`. Theme choice persists in localStorage.

### State Management

All state lives in Svelte writable/derived stores:

| Store | What it holds |
|-------|--------------|
| `filesystem` | File tree, current file, selection, expanded paths |
| `theme` | Current theme name and derived theme object |
| `settings` | Vim mode toggle |
| `platform` | `isMobile` build-time constant |

### Tauri Integration

- `tauri-plugin-fs` for native file access
- `tauri-plugin-safe-area-insets` for mobile notch handling
- Custom window (no OS decorations), with drag and close/minimize/maximize buttons
- CSP configured in `tauri.conf.json`

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/routes/+page.svelte` | Main page, routes to desktop or mobile |
| `frontend/src/routes/PageDesktop.svelte` | Desktop layout |
| `frontend/src/routes/PageMobile.svelte` | Mobile layout |
| `frontend/src/lib/components/Editor.svelte` | CodeMirror + preview |
| `frontend/src/lib/components/FileTree.svelte` | Hierarchical file browser |
| `frontend/src/lib/components/Sidebar.svelte` | Search, tree, plugin actions |
| `frontend/src/lib/stores/filesystem.ts` | File tree state and actions |
| `frontend/src/lib/stores/theme.ts` | Theme management |
| `frontend/src/lib/themes/index.ts` | Theme definitions (CSS variable maps) |
| `frontend/src-tauri/tauri.conf.json` | Tauri window and CSP config |

## Design Decisions

- **No SSR.** SvelteKit runs with `ssr: false` and static adapter. The app is fully client-side.
- **Build-time platform split.** `VITE_PLATFORM` determines desktop vs. mobile layout at build time, avoiding runtime detection.
- **Custom window chrome.** Tauri runs without OS decorations. The app draws its own title bar with drag zone and window controls.
- **Plugin-driven UI.** StatusBar, sidebar actions, and settings tabs are all rendered from plugin registrations, not hardcoded.

<!-- manual -->
<!-- /manual -->
