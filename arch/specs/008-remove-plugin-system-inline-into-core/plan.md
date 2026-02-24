# Plan: Remove Plugin System, Inline Into Core

## Tech Stack

- Language: TypeScript 5.x
- Framework: Svelte 5 (runes), SvelteKit
- Testing: Vitest + Playwright

## What Changes

Remove the entire plugin abstraction layer. The two existing plugins (Daily Notes, AI Chat) become regular features that import stores and actions directly. No more PluginContext, PluginManager, ui-registry, or dynamic component loading.

## Structure

After the refactor:

```
src/lib/
├── features/
│   ├── daily-notes/          # moved from plugins/installed/daily-notes
│   │   ├── DailyNoteButton.svelte
│   │   ├── Settings.svelte
│   │   └── state.ts          # rewritten: direct imports, no PluginContext
│   └── ai-chat/              # moved from plugins/installed/ai-chat
│       ├── ChatButton.svelte
│       ├── ChatPane.svelte
│       ├── ChatMessage.svelte
│       ├── Settings.svelte
│       ├── state.ts           # rewritten: direct imports, no PluginContext
│       ├── storage.ts         # rewritten: direct localStorage, no PluginStorage
│       ├── types.ts
│       └── providers/
│           ├── index.ts
│           └── chutes.ts
├── components/
│   ├── Sidebar.svelte         # direct import of DailyNoteButton + ChatButton
│   ├── StatusBar.svelte       # simplified: no PluginSlot
│   └── Notifications.svelte   # new: extracted from StatusBar (toast system)
├── stores/
│   └── filesystem.ts          # remove pluginManager hook dispatches
```

Deleted:
```
src/lib/plugins/               # entire directory removed
  types.ts, context.ts, loader.ts, ui-registry.ts,
  index.ts, PluginSlot.svelte,
  installed/ (moved to features/)
```

## Approach

### Step 1: Create `src/lib/features/` and move files

Move both plugin directories out of the plugin system:
- `plugins/installed/daily-notes/` → `features/daily-notes/`
- `plugins/installed/ai-chat/` → `features/ai-chat/`

Delete `manifest.json` and `index.ts` (plugin entry points) from each. These won't be needed — the features initialize via direct imports.

### Step 2: Rewrite Daily Notes state to use direct imports

`features/daily-notes/state.ts` currently accesses everything through `ctx`:
- `ctx.storage.get/set` → `localStorage.getItem/setItem` with new key prefix `basidian-daily-notes-`
- `ctx.stores.filesystem.rootNodes` → `import { rootNodes } from '$lib/stores/filesystem'`
- `ctx.actions.filesystem.*` → `import { filesystemActions } from '$lib/stores/filesystem'`
- `ctx.log.*` → `import { createLogger } from '$lib/utils/logger'`
- `ctx.ui.showNotification(...)` → `import { showNotification } from '$lib/stores/notifications'`

Remove the `setContext()`/`ctx` pattern entirely.

### Step 3: Rewrite AI Chat state and storage to use direct imports

`features/ai-chat/state.ts`:
- Remove `PluginContext` dependency
- The `chatPaneOpen` store and toggle/open/close functions already work standalone
- Delete `setContext`/`getContext` — components that used `getContext()?.log` switch to direct logger import

`features/ai-chat/storage.ts`:
- Remove `PluginStorage` abstraction
- Use `localStorage` directly with new key prefix `basidian-ai-chat-`
- Storage API methods (`get`, `set`, `remove`) become thin wrappers around `localStorage`
- Drop `initStorage()` — storage works immediately

Update `ChatButton.svelte` and `ChatPane.svelte`: replace `getContext()?.log` with direct `createLogger` import.

### Step 4: Create a lightweight notification store

Extract the toast notification system from `ui-registry.ts` into a standalone store:

`src/lib/stores/notifications.ts`:
- `notifications` writable store (array of `{id, message, type}`)
- `showNotification(message, type)` — adds notification, auto-dismisses after 5s
- `dismissNotification(id)` — manual dismiss

This is the only piece of ui-registry that features actually use (Daily Notes calls `showNotification` on note creation).

### Step 5: Update Sidebar — direct component imports

Replace the dynamic `uiRegistry.sidebarActions` subscription with direct imports:

```svelte
import DailyNoteButton from '$lib/features/daily-notes/DailyNoteButton.svelte';
import ChatButton from '$lib/features/ai-chat/ChatButton.svelte';
```

Render them directly in the sidebar-actions div. No more dynamic component loop.

### Step 6: Update StatusBar — remove PluginSlot

Current StatusBar renders `PluginSlot` and notifications from ui-registry. After this change:
- Remove `PluginSlot` import and rendering (no plugins register status bar items anyway)
- Import notifications from the new `$lib/stores/notifications` store
- If the status bar becomes empty (no status items registered by either feature), simplify to just notifications

### Step 7: Update Settings page — direct feature settings

Replace the dynamic plugin list and settings tabs with direct imports:

- Remove the "Plugins" section with enable/disable toggles
- Import `DailyNotesSettings` and `AIChatSettings` components directly
- Render them as regular settings sections

### Step 8: Update +layout.svelte — remove plugin initialization

- Remove `pluginManager.initialize()` call
- Remove `pluginManager.dispatchThemeChange()` call
- Remove `pluginManager` import

### Step 9: Update filesystem.ts — remove hook dispatches

Remove all `pluginManager.dispatch*()` calls:
- `dispatchFileOpen` in `openFile()`
- `dispatchFileSave` in `updateNode()`
- `dispatchFileCreate` in `createFile()`
- `dispatchFileDelete` in `deleteNode()`
- Remove `pluginManager` import

Neither plugin uses these hooks, so nothing breaks.

### Step 10: Delete the plugins directory

Remove `src/lib/plugins/` entirely:
- `types.ts`, `context.ts`, `loader.ts`, `ui-registry.ts`, `index.ts`, `PluginSlot.svelte`
- `installed/` (already moved in step 1)

### Step 11: Run tests and lint

Run `npm test && npm run lint` to catch any broken imports or regressions.

### Step 11.5: Migrate localStorage keys

Add a one-time migration that runs on app startup (in `+layout.svelte` or a dedicated `migrate.ts`):

- Rename `basidian-plugin-daily-notes-*` → `basidian-daily-notes-*`
- Rename `basidian-plugin-ai-chat-*` → `basidian-ai-chat-*`

Logic: iterate `localStorage` keys, match the old prefix, copy to new key, delete old key. Run once — the migration is idempotent (no-ops if old keys don't exist).

## Risks

- **Missing import paths**: Many files import from `$lib/plugins` or `$lib/plugins/types`. Grep for all occurrences before deleting. **Mitigation**: Step 11 catches these via TypeScript + lint.
- **Notification system regression**: The toast notification is used by Daily Notes and potentially by AI Chat. **Mitigation**: Extract it as a standalone store before removing ui-registry.

## Open Questions

None — the scope is clear.
