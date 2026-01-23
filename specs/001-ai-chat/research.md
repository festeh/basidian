# Research: AI Chat Plugin

**Feature**: 001-ai-chat
**Date**: 2026-01-09

## 1. Chutes AI Provider Integration

### Decision
Use Chutes AI via their OpenAI-compatible API endpoint.

### Rationale
- Chutes provides an OpenAI-compatible `/v1/chat/completions` endpoint
- Standard request/response format familiar to developers
- Supports streaming for progressive response display
- Free tier available for initial development/testing

### Technical Details

**Base URL**: `https://llm.chutes.ai/v1`
**Endpoint**: `POST /chat/completions`

**Authentication**: Bearer token in Authorization header
```
Authorization: Bearer <API_KEY>
```

**Request Format**:
```json
{
  "model": "moonshotai/Kimi-K2-Instruct-0905",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello" }
  ],
  "stream": true,
  "max_tokens": 1024,
  "temperature": 0.7
}
```

**Response Format** (non-streaming):
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "moonshotai/Kimi-K2-Instruct-0905",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**Streaming**: Uses Server-Sent Events (SSE) with `stream: true`

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| OpenAI directly | User specified Chutes as initial provider |
| Anthropic directly | User specified Chutes as initial provider |
| Backend proxy | Adds complexity; browser can call API directly |

---

## 2. Plugin Architecture Integration

### Decision
Implement as a standard Basidian plugin following the existing daily-notes pattern.

### Rationale
- Reuses proven plugin infrastructure (PluginContext, ui-registry)
- Consistent with existing plugins (daily-notes)
- Supports all required UI registration points (sidebar action, settings tab)
- Built-in storage API for persistence

### Key Integration Points

1. **Sidebar Action**: `ctx.ui.registerSidebarAction(ChatButton)` - displays AI button below search bar
2. **Settings Tab**: `ctx.ui.registerSettingsTab('ai-chat', 'AI Chat', Settings)` - configuration UI
3. **Storage**: `ctx.storage.get/set()` - persists settings and conversations
4. **Notifications**: `ctx.ui.showNotification()` - error messages, confirmations

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Custom sidebar panel | Sidebar action fits better for toggle button |
| Backend integration | Frontend-only keeps it simple, no backend changes |
| IndexedDB storage | Plugin storage API (localStorage) sufficient for chat history |

---

## 3. Chat Pane UI Pattern

### Decision
Implement chat pane as a right-side overlay panel that can be toggled open/closed.

### Rationale
- Right-side placement is standard for chat assistants
- Overlay doesn't disrupt main content layout
- Toggle pattern familiar to users
- Can be closed to focus on notes

### UI Components

1. **ChatButton.svelte**: Sidebar action button (icon-based)
2. **ChatPane.svelte**: Main chat container (right-side panel)
3. **ChatMessage.svelte**: Individual message bubble
4. **Settings.svelte**: Configuration form

### Layout Approach

```
┌─────────────────────────────────────────────────────┐
│  [Sidebar]  │  [Main Content]     │  [Chat Pane]   │
│             │                     │                 │
│  Search     │  Note Editor        │  Messages       │
│  AI Button  │                     │  Input          │
│  Files      │                     │  Send           │
└─────────────────────────────────────────────────────┘
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Modal dialog | Poor UX for ongoing conversations |
| Bottom drawer | Less screen space, awkward on desktop |
| Separate page | Breaks context, can't reference notes |

---

## 4. Conversation Storage Strategy

### Decision
Store conversations in localStorage via plugin storage API, keyed by conversation ID.

### Rationale
- Plugin storage API already namespaced per plugin
- No backend changes required
- Instant persistence (no network)
- Sufficient for personal note-taking use case

### Storage Schema

```typescript
// Key: 'conversations'
// Value: Conversation[]
[
  {
    id: "conv_1234567890",
    title: "Chat about project ideas",
    createdAt: "2026-01-09T10:00:00Z",
    updatedAt: "2026-01-09T10:30:00Z",
    messages: [
      { id: "msg_1", role: "user", content: "...", timestamp: "..." },
      { id: "msg_2", role: "assistant", content: "...", timestamp: "..." }
    ]
  }
]

// Key: 'settings'
// Value: AISettings
{
  provider: "chutes",
  apiKey: "cpk_...",
  model: "moonshotai/Kimi-K2-Instruct-0905",
  temperature: 0.7
}

// Key: 'currentConversationId'
// Value: string | null
"conv_1234567890"
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| IndexedDB | Overkill for text chat, plugin API uses localStorage |
| Backend database | Requires backend changes, adds complexity |
| File-based (notes) | Mixing chat with notes confusing |

---

## 5. Streaming Implementation

### Decision
Use native `fetch` with `ReadableStream` for streaming responses.

### Rationale
- Native browser API, no dependencies
- Works with SSE format from Chutes API
- Progressive display improves perceived performance
- Standard pattern for chat applications

### Implementation Pattern

```typescript
async function streamChat(messages: Message[], onChunk: (text: string) => void) {
  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      messages,
      stream: true,
    }),
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    // Parse SSE format: data: {...}\n\n
    const lines = chunk.split('\n').filter(line => line.startsWith('data: '));
    for (const line of lines) {
      const json = JSON.parse(line.slice(6));
      if (json.choices?.[0]?.delta?.content) {
        onChunk(json.choices[0].delta.content);
      }
    }
  }
}
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| EventSource API | Doesn't support POST requests with body |
| WebSocket | Chutes uses HTTP SSE, not WebSocket |
| No streaming | Poor UX, long wait for responses |

---

## 6. Provider Abstraction

### Decision
Create a minimal provider interface to support future providers.

### Rationale
- User requested architecture supporting multiple providers
- Minimal cost to abstract now vs refactoring later
- Single implementation (Chutes) validates the interface

### Interface Design

```typescript
interface AIProvider {
  id: string;
  name: string;
  sendMessage(
    messages: ChatMessage[],
    options: SendOptions,
    onChunk?: (text: string) => void
  ): Promise<string>;
  validateApiKey(apiKey: string): Promise<boolean>;
}

interface SendOptions {
  apiKey: string;
  model: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
}
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| No abstraction | Makes adding providers harder later |
| Full plugin system for providers | Over-engineering for initial scope |
| OpenAI SDK | Adds dependency, Chutes is compatible anyway |

---

## Summary of Decisions

| Area | Decision |
|------|----------|
| AI Provider | Chutes via OpenAI-compatible API |
| Architecture | Standard Basidian plugin |
| UI Pattern | Right-side toggle panel |
| Storage | localStorage via plugin API |
| Streaming | Native fetch + ReadableStream |
| Provider Design | Minimal interface for extensibility |
