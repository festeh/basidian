# Plugin System

## Overview

Basidian has two plugin systems: a rich frontend plugin architecture with UI slots and lifecycle hooks, and a simpler backend plugin model based on composable classes over the HTTP client.

## How It Works

### Frontend Plugins

```
PluginManager.initialize()
  │
  ├─ Scans installed/**/manifest.json via import.meta.glob
  │
  ├─ For each plugin:
  │    ├─ Creates PluginContext (stores, actions, ui, commands, storage)
  │    ├─ Calls plugin.onLoad(ctx)
  │    └─ Plugin registers UI into slots
  │
  └─ On events (file open, save, etc.):
       └─ Dispatches to all plugins with matching hooks
```

**UI Slots** — Plugins register components into named slots:

| Slot | Where it renders |
|------|-----------------|
| `statusBarItems` | Bottom status bar |
| `editorToolbarItems` | Editor toolbar |
| `sidebarActions` | Sidebar action buttons |
| `sidebarPanels` | Sidebar panel area |
| `settingsTabs` | Settings page |
| `notifications` | Toast area |

**Lifecycle hooks:**

| Hook | Fires when |
|------|-----------|
| `onLoad` | Plugin loads |
| `onUnload` | Plugin unloads |
| `onFileOpen` | A file is opened |
| `onFileSave` | A file is saved |
| `onFileCreate` | A file is created |
| `onFileDelete` | A file is deleted |
| `onThemeChange` | Theme changes |

**PluginContext** gives each plugin access to:
- Svelte stores (filesystem, settings, theme)
- Actions (filesystem mutations, theme changes)
- UI registration methods
- Command and context menu registries
- DOM access and style injection
- Scoped localStorage (`pluginId:key`)
- A logger

### Backend Plugins

Backend plugins are plain Python classes that wrap `BasidianClient`:

```python
async with BasidianClient(url) as client:
    daily = DailyNotes(client)
    today = await daily.get_or_create_today()
```

No formal registry or lifecycle — just composition.

### Installed Plugins

| Plugin | Type | What it does |
|--------|------|-------------|
| `ai-chat` | Frontend | AI chat sidebar panel with Chutes provider |
| `daily-notes` | Frontend | Create/open daily dated notes |
| `daily_notes` | Backend | Daily notes via HTTP client |

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/plugins/types.ts` | Plugin interface and manifest types |
| `frontend/src/lib/plugins/context.ts` | PluginContext factory |
| `frontend/src/lib/plugins/ui-registry.ts` | UI slot stores and registration |
| `frontend/src/lib/plugins/loader.ts` | PluginManager (load, unload, dispatch) |
| `frontend/src/lib/plugins/PluginSlot.svelte` | Renders plugin UI in a slot |
| `frontend/src/lib/plugins/installed/ai-chat/` | AI Chat plugin |
| `frontend/src/lib/plugins/installed/daily-notes/` | Daily Notes plugin |
| `backend/src/plugins/daily_notes.py` | Backend daily notes plugin |

## Design Decisions

- **Convention over configuration.** Frontend plugins live in `installed/` and are discovered via glob. No plugin marketplace or runtime installation.
- **Scoped context.** Each plugin gets its own PluginContext. Storage is namespaced. UI registrations track which plugin owns them for cleanup on unload.
- **No cross-plugin communication.** Plugins don't talk to each other directly. They interact through shared stores and the event hook system.

<!-- manual -->
<!-- /manual -->
