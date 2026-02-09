# Testing

## Overview

Two test layers cover the frontend: fast unit-level HTML snapshot tests (Vitest) and pixel-accurate visual screenshot tests (Playwright). Together they catch both structural regressions and visual regressions without a running backend.

## How It Works

```
                  Fast (< 2s)                  Visual (~5s)
              ┌────────────────┐          ┌────────────────────┐
              │    Vitest       │          │    Playwright       │
              │  jsdom + Svelte │          │  Chromium + Vite    │
              │                │          │                    │
              │  Renders HTML  │          │  Takes PNG shots   │
              │  in-memory     │          │  of real browser   │
              ├────────────────┤          ├────────────────────┤
              │  Mocks:        │          │  Mocks:            │
              │  - Tauri APIs  │          │  - Backend API via │
              │  - CodeMirror  │          │    page.route()    │
              │  - $app/*      │          │  - Tauri runtime   │
              │  - Platform    │          │    via addInitScript│
              └────────────────┘          └────────────────────┘
                     │                            │
                     ▼                            ▼
              .snap files                  .png baselines
              (committed)                  (committed)
```

### Vitest (HTML snapshots)

Renders `PageDesktop` and `PageMobile` in jsdom with pre-populated Svelte stores. Compares full HTML output against committed `.snap` files. Catches structural changes like missing elements or changed markup.

Key setup:
- Svelte 5 needs `resolve.conditions: ['browser']` in vitest config (otherwise it resolves the server bundle).
- `$app/environment` and `$app/navigation` are aliased to mock files.
- CodeMirror and MarkdownPreview are replaced with simple mock components.
- Tauri APIs are stubbed with `vi.mock()`.

### Playwright (visual screenshots)

Launches two Vite dev servers (desktop on port 5173, mobile on port 5174), each with a different `VITE_PLATFORM`. Chromium navigates to the real app, interacts with it, and takes PNG screenshots.

Key setup:
- Backend API calls are intercepted with `page.route()` and return fixture data.
- Tauri runtime is stubbed via `page.addInitScript()` (sets `window.__TAURI_INTERNALS__`).
- Route registration order matters: catch-all routes go first, specific routes last (Playwright uses last-match-wins).
- `reducedMotion: 'reduce'` disables animations for deterministic screenshots.

## Key Files

| File | Purpose |
|------|---------|
| `frontend/vitest.config.ts` | Vitest config: Svelte plugin, jsdom, aliases, env |
| `frontend/src/tests/setup.ts` | Global test setup: Tauri/CodeMirror/FS plugin mocks |
| `frontend/src/tests/fixtures.ts` | Fake file tree and note data for vitest |
| `frontend/src/tests/snapshots/desktop.test.ts` | Desktop HTML snapshot tests |
| `frontend/src/tests/snapshots/mobile.test.ts` | Mobile HTML snapshot tests |
| `frontend/playwright.config.ts` | Playwright config: two dev servers, two projects |
| `frontend/e2e/fixtures.ts` | Flat API response data for Playwright |
| `frontend/e2e/visual.spec.ts` | Visual screenshot tests (6 scenarios) |

## Test Scenarios

### Vitest snapshots (6 tests)

| Platform | Scenario |
|----------|----------|
| Desktop | Empty state, note open, loading state |
| Mobile | Empty state, note open, loading state |

### Playwright screenshots (6 tests)

| Platform | Scenario |
|----------|----------|
| Desktop | Empty state, note open, sidebar collapsed |
| Mobile | Empty state, note open, sidebar overlay |

## Design Decisions

- **Two test layers, not one.** Vitest snapshots run in milliseconds and catch structural changes. Playwright screenshots catch visual issues (CSS, layout, theming) that HTML snapshots miss. See [ADR-001](adr/001_two_tier_testing.md).
- **No backend required.** Both layers mock all API calls. Tests run without starting the Python backend.
- **Fixture data is flat for Playwright.** The backend returns flat node lists; `buildTree()` in the frontend does the nesting. Playwright fixtures match the real API shape. Vitest fixtures are pre-nested since they bypass the API and set stores directly.
- **Chromium only.** Visual tests run on Chromium. Cross-browser testing adds cost with little value for a Tauri app.

<!-- manual -->
<!-- /manual -->
