# Tasks: AI Chat Plugin

**Input**: Design documents from `/specs/001-ai-chat/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per constitution (Principle I: Testable Design - tests optional, testability required).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Plugin location**: `frontend/src/lib/plugins/installed/ai-chat/`
- All paths are relative to repository root unless specified

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create plugin directory structure and core type definitions

- [x] T001 Create plugin directory at frontend/src/lib/plugins/installed/ai-chat/
- [x] T002 Create manifest.json with plugin metadata (id: ai-chat, name: AI Chat, version: 1.0.0, hooks: onLoad/onUnload) in frontend/src/lib/plugins/installed/ai-chat/manifest.json
- [x] T003 [P] Create types.ts with all TypeScript interfaces (copy from specs/001-ai-chat/contracts/types.ts) in frontend/src/lib/plugins/installed/ai-chat/types.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create storage.ts with conversation persistence helpers (getConversations, saveConversation, deleteConversation, getSettings, saveSettings) in frontend/src/lib/plugins/installed/ai-chat/storage.ts
- [x] T005 [P] Create providers/index.ts with AIProvider interface and provider registry in frontend/src/lib/plugins/installed/ai-chat/providers/index.ts
- [x] T006 [P] Create providers/chutes.ts implementing ChutesProvider with sendMessage (streaming) and validateApiKey in frontend/src/lib/plugins/installed/ai-chat/providers/chutes.ts
- [x] T007 Create index.ts with plugin lifecycle hooks (onLoad registers sidebar action + settings tab, onUnload unregisters) in frontend/src/lib/plugins/installed/ai-chat/index.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic AI Conversation (Priority: P1) 🎯 MVP

**Goal**: User can click AI button in sidebar, open chat pane, send message, receive AI response

**Independent Test**: Enable plugin, click AI button, send "Hello", verify response appears with loading indicator

### Implementation for User Story 1

- [x] T008 [P] [US1] Create ChatButton.svelte with AI icon button that toggles chat pane visibility in frontend/src/lib/plugins/installed/ai-chat/ChatButton.svelte
- [x] T009 [P] [US1] Create ChatMessage.svelte displaying single message (user vs assistant styling, timestamp) in frontend/src/lib/plugins/installed/ai-chat/ChatMessage.svelte
- [x] T010 [US1] Create ChatPane.svelte with right-side panel layout (header with close button, message list, input area) in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T011 [US1] Implement message sending in ChatPane.svelte (create user message, call provider, stream response, update UI)
- [x] T012 [US1] Add loading indicator during AI response generation in ChatPane.svelte
- [x] T013 [US1] Add error handling for API failures with retry option in ChatPane.svelte
- [x] T014 [US1] Wire ChatButton to toggle ChatPane visibility via shared state in index.ts

**Checkpoint**: User Story 1 complete - can send messages and receive AI responses

---

## Phase 4: User Story 2 - Conversation History (Priority: P2)

**Goal**: Conversations persist across sessions, user can scroll history, start new conversations

**Independent Test**: Have conversation, reload app, verify messages still visible; click New Conversation, verify old conversation preserved

### Implementation for User Story 2

- [x] T015 [US2] Add conversation loading from storage on ChatPane mount in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T016 [US2] Add auto-save after each message (user and assistant) to storage in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T017 [US2] Add scrollable message list with auto-scroll to bottom on new messages in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T018 [US2] Add "New Conversation" button in ChatPane header that creates fresh conversation in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T019 [US2] Add conversation list sidebar (optional toggle) showing past conversations with titles in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T020 [US2] Add delete conversation with confirmation dialog in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte

**Checkpoint**: User Story 2 complete - conversations persist and can be managed

---

## Phase 5: User Story 3 - Plugin Configuration (Priority: P3)

**Goal**: User can configure API key, select provider/model in settings

**Independent Test**: Go to Settings, find AI Chat tab, enter API key, save, verify key persists after reload; try sending without key, verify error prompts to configure

### Implementation for User Story 3

- [x] T021 [US3] Create Settings.svelte with provider selection dropdown in frontend/src/lib/plugins/installed/ai-chat/Settings.svelte
- [x] T022 [US3] Add API key input field with show/hide toggle in Settings.svelte
- [x] T023 [US3] Add model selection dropdown (populated from provider config) in Settings.svelte
- [x] T024 [US3] Add temperature slider (0.0-2.0) in Settings.svelte
- [x] T025 [US3] Add "Validate API Key" button with visual feedback (valid/invalid) in Settings.svelte
- [x] T026 [US3] Wire settings to storage (auto-save on change) in Settings.svelte
- [x] T027 [US3] Add "Configure API Key" prompt in ChatPane when no key is set, linking to settings

**Checkpoint**: User Story 3 complete - full configuration available in settings

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 Add keyboard shortcuts (Enter to send, Escape to close pane) in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T029 Add empty state message when no conversations exist in frontend/src/lib/plugins/installed/ai-chat/ChatPane.svelte
- [x] T030 Add CSS styling with theme support (var(--color-*) custom properties) across all components
- [x] T031 Run quickstart.md validation checklist to verify all acceptance criteria

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 (P1): Can start after Phase 2
  - US2 (P2): Can start after Phase 2 (independent of US1)
  - US3 (P3): Can start after Phase 2 (independent of US1/US2)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Requires Phase 2 complete. No dependencies on other stories.
- **User Story 2 (P2)**: Requires Phase 2 complete. Builds on US1 components but can be tested independently.
- **User Story 3 (P3)**: Requires Phase 2 complete. Independent of US1/US2 for implementation.

### Within Each User Story

- Components with [P] can be created in parallel
- ChatPane is the main integration point for US1/US2
- Settings.svelte is standalone for US3

### Parallel Opportunities

- T002, T003 can run in parallel (different files)
- T005, T006 can run in parallel (different files)
- T008, T009 can run in parallel (different components)
- All three user stories CAN run in parallel after Phase 2 (if team capacity allows)

---

## Parallel Example: Phase 2 Foundation

```bash
# Launch these tasks in parallel:
Task: "Create providers/index.ts with AIProvider interface"
Task: "Create providers/chutes.ts implementing ChutesProvider"
```

## Parallel Example: User Story 1 Components

```bash
# Launch these tasks in parallel:
Task: "Create ChatButton.svelte with AI icon button"
Task: "Create ChatMessage.svelte displaying single message"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T014)
4. **STOP and VALIDATE**: Test basic conversation flow
5. Deploy/demo if ready - core value delivered!

### Incremental Delivery

1. Setup + Foundational → Plugin structure ready
2. User Story 1 → Basic chat works → MVP Complete
3. User Story 2 → History persists → Enhanced value
4. User Story 3 → Settings available → Full feature
5. Polish → Production ready

### Recommended Order (Solo Developer)

1. T001 → T002 → T003 (Setup)
2. T004 → T005+T006 (parallel) → T007 (Foundation)
3. T008+T009 (parallel) → T010 → T011 → T012 → T013 → T014 (US1 MVP)
4. T015 → T016 → T017 → T018 → T019 → T020 (US2 History)
5. T021 → T022 → T023 → T024 → T025 → T026 → T027 (US3 Settings)
6. T028 → T029 → T030 → T031 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable at its checkpoint
- Commit after each task or logical group
- Use Svelte 5 runes ($state, $derived) for all reactive state
- Use CSS custom properties for theming (var(--color-*))
- All storage via ctx.storage API (automatically prefixed)
