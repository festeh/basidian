# Plan: Mobile and Desktop Layout Components

**Spec**: specs/003-mobile-desktop-layout-components/spec.md

## Tech Stack

- Language: TypeScript
- Framework: Svelte 5 (runes), SvelteKit, Tauri 2
- Testing: npm test + npm run lint
- Platform detection: `VITE_PLATFORM` env var (already implemented)

## Structure

```
frontend/src/lib/
├── stores/
│   └── platform.ts                    # NEW: isMobile constant
├── components/
│   ├── TopBar.svelte                  # KEEP: shared topbar buttons (info, settings)
│   ├── TopBarDesktop.svelte           # NEW: desktop shell (dragging, window controls, chevron)
│   ├── TopBarMobile.svelte            # NEW: mobile shell (hamburger, no window controls)
│   ├── Sidebar.svelte                 # NO CHANGE (shared, parent controls positioning)
│   ├── Backdrop.svelte                # NEW: click-to-close overlay
│   ├── Editor.svelte                  # NO CHANGE
│   └── StatusBar.svelte               # NO CHANGE
├── plugins/
│   └── installed/
│       └── ai-chat/
│           └── ChatPane.svelte        # MODIFY: full-screen on mobile
frontend/src/
├── routes/
│   ├── +page.svelte                   # MODIFY: pick desktop or mobile layout
│   ├── PageDesktop.svelte             # NEW: desktop layout (sidebar in flexbox)
│   └── PageMobile.svelte              # NEW: mobile layout (sidebar as overlay)
└── lib/
    └── page-shared.ts                 # NEW: shared logic (create file/folder handlers)
```

## Component split decisions

### TopBar — Split into 3 files

**Why split:** ~80% different between platforms. Desktop has window dragging, chevron toggle, minimize/maximize/close. Mobile has hamburger icon, no window controls, no dragging. Only info and settings buttons are shared.

**How to share:** Extract the shared buttons (info, settings) into the existing `TopBar.svelte` as a snippet or child component. `TopBarDesktop.svelte` and `TopBarMobile.svelte` each compose it with their own shell.

**Tradeoff:** 3 files instead of 1. Each file is simple and single-purpose. Adding a new topbar button means adding it once in the shared part.

### +page.svelte — Split into 3 files

**Why split:** The layout structure is fundamentally different. Desktop uses inline flexbox with a collapsible sidebar. Mobile uses a full-screen editor with an overlay sidebar + backdrop. Cramming both into one file with `{#if isMobile}` would make neither layout readable.

**How to share:** Extract the non-layout logic (create file modal, create folder modal, modal handlers) into `page-shared.ts`. Both page components import these handlers. `+page.svelte` becomes a thin router that picks `PageDesktop` or `PageMobile` based on `isMobile`.

**Tradeoff:** 3 files instead of 1. The shared module avoids duplicating modal logic. Each layout file is clean and focused on one rendering path.

### Sidebar — Keep shared

**Why keep:** Same content on both platforms (search, actions, file tree). Only the positioning context changes, and that's the parent's job.

### ChatPane — Keep shared

**Why keep:** Same logic, same structure. Only difference is `width: 100%` on mobile. One CSS class toggle, not worth splitting 280+ lines.

### Editor, StatusBar — Keep shared

**Why keep:** No mobile-specific changes needed.

## Approach

### 1. Platform constant (`platform.ts`)

```ts
export const isMobile = import.meta.env.VITE_PLATFORM === 'mobile';
```

Plain constant, not a store. Never changes at runtime.

### 2. Shared page logic (`page-shared.ts`)

Extract from current `+page.svelte`:
- `createFile()` handler
- `createFolder()` handler
- `handleModalKeydown()` helper
- Reactive state for modals (`showCreateFileModal`, `showCreateFolderModal`, `newItemName`, `isCreating`)

Both `PageDesktop.svelte` and `PageMobile.svelte` import and use these. The modal markup stays in each page component (it's just `<Modal>` tags — small and declarative).

### 3. Page router (`+page.svelte`)

Becomes a thin wrapper:

```svelte
{#if isMobile}
  <PageMobile />
{:else}
  <PageDesktop />
{/if}
```

### 4. Desktop layout (`PageDesktop.svelte`)

Current `+page.svelte` behavior, unchanged:
- Flexbox with inline sidebar (280px, collapsible)
- `TopBarDesktop` with chevron toggle, window controls, dragging
- Editor fills remaining space
- StatusBar at bottom

### 5. Mobile layout (`PageMobile.svelte`)

- Full-screen editor as the base layer
- `TopBarMobile` with hamburger icon
- `sidebarOpen` state controls overlay visibility
- When open: `Backdrop` component + `Sidebar` in a fixed container sliding in from left
- Watch `currentFile` store — when it changes, set `sidebarOpen = false` (auto-close on file select)

### 6. TopBar shared part (`TopBar.svelte`)

Refactor current TopBar to export just the shared buttons (info, settings) as a component or snippet. Both `TopBarDesktop` and `TopBarMobile` compose it.

### 7. TopBar desktop (`TopBarDesktop.svelte`)

Current TopBar behavior:
- `startDragging` on mousedown
- Left: chevron sidebar toggle
- Right: shared buttons (via `TopBar`) + window controls (minimize, maximize, close)

### 8. TopBar mobile (`TopBarMobile.svelte`)

- No dragging
- Left: hamburger icon (fires `onToggleSidebar`)
- Right: shared buttons (via `TopBar`), no window controls

### 9. Backdrop (`Backdrop.svelte`)

Generic overlay component (not mobile-specific in name — could be reused):
- `position: fixed; inset: 0`
- Semi-transparent background
- Fires `onClose` on click
- `z-index: 99`

### 10. Sidebar in overlay context

No changes to `Sidebar.svelte` itself. On mobile, `PageMobile.svelte` wraps it in a fixed container:
- `position: fixed; left: 0; top: 0; bottom: 0; width: 280px; z-index: 100`
- CSS transition for slide-in/out
- Respects safe area insets

### 11. ChatPane full-screen on mobile

- Import `isMobile` from platform store
- Add `class:mobile={isMobile}` to `.chat-pane`
- Replace `@media (max-width: 480px)` with `.chat-pane.mobile { width: 100%; }`

### 12. Safe area insets

Already implemented. Mobile sidebar overlay should apply `padding-top: var(--safe-area-inset-top)` and `padding-left: var(--safe-area-inset-left)`.

## File-by-file changes

| File | Change |
|------|--------|
| `src/lib/stores/platform.ts` | **New.** Export `isMobile` constant. |
| `src/lib/page-shared.ts` | **New.** Shared modal logic extracted from `+page.svelte`. |
| `src/routes/+page.svelte` | **Rewrite.** Thin router: pick `PageDesktop` or `PageMobile`. |
| `src/routes/PageDesktop.svelte` | **New.** Current desktop layout + `TopBarDesktop`. |
| `src/routes/PageMobile.svelte` | **New.** Mobile layout with overlay sidebar + `TopBarMobile`. |
| `src/lib/components/TopBar.svelte` | **Refactor.** Shared buttons only (info, settings). |
| `src/lib/components/TopBarDesktop.svelte` | **New.** Desktop shell: dragging, chevron, window controls + shared TopBar. |
| `src/lib/components/TopBarMobile.svelte` | **New.** Mobile shell: hamburger + shared TopBar. |
| `src/lib/components/Backdrop.svelte` | **New.** Generic click-to-close overlay. |
| `src/lib/components/Sidebar.svelte` | **No change.** |
| `src/lib/components/Editor.svelte` | **No change.** |
| `src/lib/components/StatusBar.svelte` | **No change.** |
| `src/lib/plugins/installed/ai-chat/ChatPane.svelte` | **Modify.** Platform-based full-screen. |

## Risks

- **VITE_PLATFORM not set during dev**: Vite config already throws if missing. No runtime risk.
- **Touch targets too small on mobile**: Current icon buttons are 32x32px (recommended: 44x44px). Mitigation: `TopBarMobile` uses larger touch targets.
- **Sidebar overlay z-index conflicts**: ChatPane uses `z-index: 1000`. Backdrop uses 99, sidebar overlay uses 100. Plugin panels layer on top if both are open.
- **Shared logic drift**: If `page-shared.ts` grows too large, the extraction becomes a maintenance burden. Mitigation: keep it focused on modal handlers only. Layout logic stays in each page component.

## Open Questions

None — all decisions are made.
