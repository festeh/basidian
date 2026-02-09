# ADR-001: Two-tier frontend testing (Vitest + Playwright)

**Date:** 2026-02-09
**Status:** Accepted

## Context

The frontend is a SvelteKit app with Tauri integration, platform-dependent layouts, and a rich editor (CodeMirror). We need tests that catch both structural regressions (changed HTML) and visual regressions (broken CSS, misaligned layout). A single approach can't cover both well:

- HTML snapshots are fast but blind to styling.
- Browser-based screenshot tests are thorough but slow and require a dev server.

## Decision

Use two complementary test layers:

1. **Vitest + jsdom** for fast HTML snapshot tests. Renders components in-memory with mocked stores. Runs in under 2 seconds.
2. **Playwright + Chromium** for pixel-accurate visual screenshot tests. Launches real Vite dev servers, intercepts API calls, and captures PNGs. Runs in about 5 seconds.

Each layer has its own fixture data shaped for its mocking strategy (pre-nested stores for Vitest, flat API responses for Playwright).

## Consequences

- Developers get fast feedback from `npm test` (Vitest) and can run `npm run test:visual` for deeper visual checks.
- Two sets of test fixtures to maintain, but they're small and stable.
- Playwright needs Chromium installed (`npx playwright install chromium`).
- CI will need both test commands. Visual tests may need snapshot updates when intentional UI changes land.
