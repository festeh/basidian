# Architecture Map

## Docs

| # | Doc | Summary |
|---|-----|---------|
| 01 | [System Architecture](01_system_arch.md) | Overall structure: Tauri + SvelteKit frontend, FastAPI + SQLite backend, CLI tools |
| 02 | [Database](02_database.md) | SQLite schema (notes, fs_nodes), async access, path-based hierarchy |
| 03 | [API](03_api.md) | REST endpoints for notes and filesystem CRUD |
| 04 | [Plugin System](04_plugin_system.md) | Frontend UI slots and lifecycle hooks, backend composable classes |
| 05 | [CLI Tools](05_cli_tools.md) | basidian-server, bscli, basync — all HTTP-based |
| 06 | [Frontend UI](06_frontend_ui.md) | Svelte 5 components, theming, CodeMirror editor, Tauri integration |

## Decision Records

No ADRs recorded yet.

## Specs

| Branch | Spec | Plan |
|--------|------|------|
| [001-ai-chat](specs/001-ai-chat/spec.md) | Yes | [Yes](specs/001-ai-chat/plan.md) |
| [002-add-logging-observability](specs/002-add-logging-observability/spec.md) | Yes | [Yes](specs/002-add-logging-observability/plan.md) |
| [002-basync-cli](specs/002-basync-cli/spec.md) | Yes | [Yes](specs/002-basync-cli/plan.md) |
| [003-mobile-desktop-layout-components](specs/003-mobile-desktop-layout-components/spec.md) | Yes | [Yes](specs/003-mobile-desktop-layout-components/plan.md) |
| [004-decompose-server](specs/004-decompose-server-into-server-code-and-cli-apps/plan.md) | No | [Yes](specs/004-decompose-server-into-server-code-and-cli-apps/plan.md) |
| [005-daily-notes-plugin](specs/005-extend-basidian-client-with-today-note-plugin-for-/plan.md) | No | [Yes](specs/005-extend-basidian-client-with-today-note-plugin-for-/plan.md) |
