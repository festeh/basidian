# Implementation Plan: AI Chat Plugin

**Branch**: `001-ai-chat` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-chat/spec.md`

## Summary

Implement an AI Chat plugin for Basidian that adds a sidebar action button (below the search bar) to open a right-side chat pane. Users can converse with AI (initially Chutes provider), with conversation history persisted in localStorage. The plugin follows the existing Basidian plugin architecture using Svelte 5 and TypeScript.

## Technical Context

**Language/Version**: TypeScript 5.x, Svelte 5 (runes)
**Primary Dependencies**: Svelte 5, existing plugin system (PluginContext, ui-registry)
**Storage**: localStorage via plugin storage API (ctx.storage)
**Testing**: Manual testing (tests optional per constitution)
**Target Platform**: Web (cross-platform via Flutter WebView), Desktop
**Project Type**: Web application (frontend plugin)
**Performance Goals**: <3s initial AI response, <2s history load
**Constraints**: Must work within existing plugin architecture, no backend changes required
**Scale/Scope**: Single user, unlimited conversations stored locally

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Testable Design | PASS | Plugin uses injectable PluginContext, pure functions for settings/storage, isolated Svelte components with clear props |
| II. Balanced Architecture | PASS | Frontend-only plugin, no backend changes needed. AI calls go directly to external provider |
| III. Pragmatic Simplicity | PASS | Single provider (Chutes) initially, localStorage for persistence, minimal abstractions |

**All gates pass.** Proceeding with implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-chat/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal TypeScript interfaces)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
└── src/
    └── lib/
        └── plugins/
            └── installed/
                └── ai-chat/
                    ├── manifest.json       # Plugin metadata
                    ├── index.ts            # Main plugin logic, lifecycle hooks
                    ├── ChatButton.svelte   # Sidebar action button
                    ├── ChatPane.svelte     # Right-side chat pane
                    ├── ChatMessage.svelte  # Individual message component
                    ├── Settings.svelte     # Settings tab component
                    ├── types.ts            # TypeScript interfaces
                    ├── storage.ts          # Conversation persistence helpers
                    └── providers/
                        ├── index.ts        # Provider abstraction
                        └── chutes.ts       # Chutes API integration
```

**Structure Decision**: Plugin-only implementation within existing frontend plugin architecture. No backend changes required as AI API calls are made directly from the browser to external providers.

## Complexity Tracking

No violations. Design follows pragmatic simplicity:
- Single provider initially (Chutes), abstraction layer allows future providers
- localStorage persistence (no database)
- Minimal component hierarchy
