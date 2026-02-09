# Plan: Snapshot Tests for Desktop & Mobile Screens

**Branch**: 006-snapshot-tests-for-desktop-mobile-screens

## Tech Stack

- Language: TypeScript
- Framework: Vitest + `@testing-library/svelte` (Svelte 5 compatible)
- Snapshot format: Vitest inline/file snapshots (HTML string snapshots)
- Testing: `vitest` via `npm test`

## Structure

Where code will live:

```
frontend/
├── vitest.config.ts              # Vitest config with Svelte + env mocking
├── src/
│   └── tests/
│       ├── setup.ts              # Global test setup (mock stores, API, Tauri)
│       ├── fixtures.ts           # Fake FsNode trees and file content
│       └── snapshots/
│           ├── desktop.test.ts   # Desktop layout snapshots
│           └── mobile.test.ts    # Mobile layout snapshots
```

## Approach

### 1. Install test dependencies

Add vitest, jsdom, @testing-library/svelte, and svelte test utilities.

### 2. Configure vitest

Create `vitest.config.ts` in `frontend/`. Key decisions:
- Use `jsdom` environment (not happy-dom — better CSS/layout support)
- Set `VITE_PLATFORM` env var per test file to control desktop vs mobile
- Alias `$lib`, `$app/navigation`, `$app/environment` to mocks
- Use the existing `svelte.config.js` via `@sveltejs/vite-plugin-svelte`

### 3. Mock external dependencies

Create `setup.ts` that stubs:
- **`$app/navigation`**: Mock `goto` as a no-op
- **`$app/environment`**: Set `browser = true`
- **`$lib/api/client`**: Mock `api` to return fake data from fixtures (no real HTTP)
- **`$lib/plugins/loader`**: Mock `pluginManager` with no-op lifecycle hooks
- **`$lib/utils/safe-area`**: Mock `applySafeAreaInsets` as no-op
- **Tauri APIs**: Not needed — components check `__TAURI__` and fall back gracefully
- **CodeMirror**: Mock `CodeMirrorEditor.svelte` as a simple `<div>` — CodeMirror relies on real DOM APIs that jsdom can't handle

### 4. Create fake data fixtures

`fixtures.ts` provides realistic FsNode trees to populate the sidebar and editor:

- **File tree**: A folder structure with ~8 nodes (2 folders, 6 files) covering nested hierarchy, markdown files with content
- **Open file**: A markdown note with headings, lists, and code blocks (simulates "note open in editor")
- **Empty state**: No file selected (simulates fresh app launch)

Example fixture:
```typescript
export const fakeTree: FsNode[] = [
  { type: 'folder', name: 'Projects', path: '/Projects', parent_path: '/', sort_order: 0, children: [...] },
  { type: 'folder', name: 'Daily', path: '/Daily', parent_path: '/', sort_order: 1, children: [...] },
  { type: 'file', name: 'Welcome.md', path: '/Welcome.md', parent_path: '/', sort_order: 2 }
];

export const fakeNote: FsNode = {
  type: 'file', name: 'Meeting Notes.md', path: '/Projects/Meeting Notes.md',
  parent_path: '/Projects', sort_order: 0,
  content: '# Meeting Notes\n\n- Discuss roadmap\n- Review PRs\n...'
};
```

### 5. Write desktop snapshot tests

`desktop.test.ts` sets `VITE_PLATFORM=desktop` and renders:

| Test | What it shows |
|------|---------------|
| `desktop: empty state` | Sidebar with file tree + editor showing "Select a file to edit" |
| `desktop: note open` | Sidebar + editor header with filename + editor body |
| `desktop: sidebar collapsed` | Editor only, no sidebar |

Each test:
1. Pre-populates stores (`rootNodes`, `currentFile`) with fixture data
2. Renders `PageDesktop` component
3. Calls `expect(container).toMatchSnapshot()`

### 6. Write mobile snapshot tests

`mobile.test.ts` sets `VITE_PLATFORM=mobile` and renders:

| Test | What it shows |
|------|---------------|
| `mobile: empty state` | Top bar with hamburger + editor empty state |
| `mobile: note open` | Top bar + editor with note content |
| `mobile: sidebar open` | Overlay sidebar + backdrop visible |

Same pattern: populate stores, render `PageMobile`, snapshot.

### 7. Add test script to package.json

Add `"test"` script: `"vitest run"` and `"test:watch"`: `"vitest"`.

### 8. Platform variable handling

The tricky part: `isMobile` is a build-time constant from `import.meta.env.VITE_PLATFORM`.

Strategy: In `vitest.config.ts`, set `define: { 'import.meta.env.VITE_PLATFORM': '"desktop"' }` as the default. For mobile tests, use `vi.mock('$lib/stores/platform', ...)` to override `isMobile = true`. This avoids needing separate vitest configs.

## Risks

- **CodeMirror in jsdom**: CodeMirror needs real DOM measurement APIs. Mitigation: mock `CodeMirrorEditor.svelte` with a simple div that shows the content text. The snapshot captures layout structure, not editor internals.
- **Svelte 5 runes + testing-library compatibility**: `@testing-library/svelte` v5 supports Svelte 5, but runes in `.svelte.ts` files may need the Svelte Vite plugin configured correctly. Mitigation: use `@sveltejs/vite-plugin-svelte` in vitest config.
- **Snapshot brittleness**: HTML snapshots break on any markup change. Mitigation: snapshot only the page-level components (PageDesktop, PageMobile), not individual leaf components. Keep fixture data minimal and stable.
- **SvelteKit module resolution**: `$lib` and `$app/*` aliases need manual setup in vitest since we're not running inside SvelteKit. Mitigation: configure `resolve.alias` in vitest config pointing to src/lib and mock modules for `$app/*`.

## Open Questions

- None — the approach is straightforward. We mock what we can't render (CodeMirror, Tauri), populate stores with fixtures, and snapshot the DOM output.
