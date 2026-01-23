# Quickstart: AI Chat Plugin

**Feature**: 001-ai-chat
**Date**: 2026-01-09

## Prerequisites

- Basidian frontend running locally (`just dev-local-linux` or `just dev-local-android`)
- A Chutes AI API key (get one at [chutes.ai](https://chutes.ai))

## Installation

The AI Chat plugin is installed by default in:
```
frontend/src/lib/plugins/installed/ai-chat/
```

## Configuration

1. Open Basidian
2. Go to **Settings** (gear icon)
3. Find the **AI Chat** section
4. Enter your Chutes API key
5. (Optional) Select a different model or adjust temperature

## Usage

### Starting a Conversation

1. Look for the **AI button** in the sidebar (below the search bar)
2. Click to open the chat pane on the right side
3. Type your message in the input field
4. Press Enter or click Send

### Conversation Features

- **New Conversation**: Click the "+" button to start fresh
- **History**: Scroll up to see previous messages
- **Delete**: Click the trash icon on a conversation to remove it
- **Close**: Click X or click the AI button again to close the pane

### Tips

- The AI can help with brainstorming, writing, and answering questions
- Conversations are saved automatically and persist across sessions
- Each conversation is independent - start a new one for different topics

## Verification Steps

After implementation, verify the following works:

### P1: Basic AI Conversation
- [ ] AI button appears in sidebar when plugin is enabled
- [ ] Clicking button opens chat pane on right side
- [ ] Can type and send a message
- [ ] AI response appears (with loading indicator during generation)
- [ ] Can close the pane

### P2: Conversation History
- [ ] Messages persist after closing and reopening the pane
- [ ] Messages persist after reloading the app
- [ ] Can scroll to view older messages
- [ ] Can start a new conversation
- [ ] Previous conversations remain accessible

### P3: Plugin Configuration
- [ ] Settings tab appears under AI Chat
- [ ] Can enter and save API key
- [ ] Error shown when trying to send without API key
- [ ] Can change model selection
- [ ] Settings persist after reload

### Edge Cases
- [ ] Empty message: Send button is disabled
- [ ] API error: User-friendly error message displayed
- [ ] Invalid API key: Clear authentication error shown
- [ ] Long response: Streams progressively
- [ ] Close during response: Response continues, visible when reopened
- [ ] Plugin disabled: Button disappears, pane closes

## Troubleshooting

### "API key required" error
- Go to Settings > AI Chat and enter your Chutes API key

### No response from AI
- Check your internet connection
- Verify your API key is valid at chutes.ai
- Check browser console for error details

### Chat pane not opening
- Ensure the AI Chat plugin is enabled in Settings
- Try refreshing the page
- Check browser console for errors

### Conversations not saving
- Check browser localStorage isn't full
- Ensure you're not in private/incognito mode
- Check for JavaScript errors in console

## Development

### File Structure
```
frontend/src/lib/plugins/installed/ai-chat/
├── manifest.json       # Plugin metadata
├── index.ts            # Main plugin, lifecycle hooks
├── ChatButton.svelte   # Sidebar action
├── ChatPane.svelte     # Main chat UI
├── ChatMessage.svelte  # Message display
├── Settings.svelte     # Configuration UI
├── types.ts            # TypeScript interfaces
├── storage.ts          # Persistence helpers
└── providers/
    ├── index.ts        # Provider abstraction
    └── chutes.ts       # Chutes implementation
```

### Key APIs Used
- `ctx.ui.registerSidebarAction()` - Add button to sidebar
- `ctx.ui.registerSettingsTab()` - Add settings tab
- `ctx.storage.get/set()` - Persist data
- `ctx.ui.showNotification()` - Show errors/confirmations
- `ctx.log.info/error()` - Logging

### Adding a New Provider

1. Create `providers/newprovider.ts` implementing `AIProvider`
2. Add provider config to `PROVIDERS` in `types.ts`
3. Provider will appear in settings dropdown
