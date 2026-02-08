# Data Model: AI Chat Plugin

**Feature**: 001-ai-chat
**Date**: 2026-01-09

## Entities

### Conversation

A collection of messages between the user and AI assistant.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | Unique identifier | Format: `conv_{timestamp}`, required |
| title | string \| null | Optional display title | Auto-generated from first message if null |
| createdAt | string | ISO 8601 timestamp | Required, immutable |
| updatedAt | string | ISO 8601 timestamp | Required, updated on each message |
| messages | Message[] | Ordered list of messages | Required, min 0 |

**Lifecycle**:
- Created: When user sends first message in new conversation
- Updated: After each message (user or AI)
- Deleted: Manual deletion by user (with confirmation)

### Message

A single exchange in a conversation.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | Unique identifier | Format: `msg_{timestamp}_{index}`, required |
| role | 'user' \| 'assistant' \| 'system' | Message sender type | Required |
| content | string | Message text content | Required, non-empty for user/assistant |
| timestamp | string | ISO 8601 timestamp | Required |
| status | 'sending' \| 'sent' \| 'error' | Delivery status | Required for user messages |
| error | string \| null | Error message if failed | Only when status === 'error' |

**Lifecycle**:
- User message: Created with status 'sending', transitions to 'sent' or 'error'
- Assistant message: Created incrementally during streaming, finalized when complete
- System message: Optional, set at conversation start

### AISettings

User configuration for the AI chat plugin.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| provider | string | Selected AI provider | Default: 'chutes', required |
| apiKey | string \| null | Provider API key | Sensitive, stored locally |
| model | string | Model identifier | Provider-specific, required |
| temperature | number | Response randomness | Range: 0.0-2.0, default: 0.7 |
| maxTokens | number | Max response length | Range: 1-4096, default: 1024 |
| systemPrompt | string \| null | Custom system message | Optional |

### ProviderConfig

Configuration for a specific AI provider.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string | Provider identifier | Required, unique |
| name | string | Display name | Required |
| baseUrl | string | API base URL | Required, valid URL |
| models | string[] | Available model IDs | Required, min 1 |
| defaultModel | string | Default model selection | Must be in models array |

## Storage Keys

All stored via `ctx.storage` with automatic `basidian-plugin-ai-chat-` prefix.

| Key | Type | Description |
|-----|------|-------------|
| `settings` | AISettings | User configuration |
| `conversations` | Conversation[] | All conversations |
| `currentConversationId` | string \| null | Active conversation |

## Relationships

```
AISettings
    └── provider ──references──> ProviderConfig.id

Conversation
    └── messages[] ──contains──> Message[]

Message
    └── role ──enum──> 'user' | 'assistant' | 'system'
```

## Validation Rules

### Conversation
- `id` must be unique across all conversations
- `messages` array maintains chronological order by timestamp
- `title` auto-generated as first 50 chars of first user message if not set

### Message
- User messages must have non-empty `content`
- Assistant messages may have empty `content` during streaming
- `timestamp` must be valid ISO 8601

### AISettings
- `apiKey` required before sending messages (FR-012)
- `temperature` clamped to 0.0-2.0 range
- `model` must be valid for selected provider

## State Transitions

### Message Status

```
[User sends message]
        │
        ▼
    'sending' ────────────────┐
        │                     │
        ▼                     ▼
     'sent'               'error'
  (AI responds)        (API failure)
```

### Conversation Lifecycle

```
[New conversation]
        │
        ▼
    created ──────────────────┐
        │                     │
        ▼                     │
    active ◄──────────────────┤
        │                     │
        ▼                     │
    (user continues)          │
        │                     │
        ▼                     │
    updated ──────────────────┘
        │
        ▼
    [User deletes]
        │
        ▼
    removed
```

## Initial Provider Data

### Chutes Provider

```typescript
const chutesProvider: ProviderConfig = {
  id: 'chutes',
  name: 'Chutes AI',
  baseUrl: 'https://llm.chutes.ai/v1',
  models: [
    'moonshotai/Kimi-K2-Instruct-0905',
    'deepseek-ai/DeepSeek-V3-0324',
    'Qwen/Qwen3-235B-A22B'
  ],
  defaultModel: 'deepseek-ai/DeepSeek-V3-0324'
};
```

## Example Data

### Stored Conversation

```json
{
  "id": "conv_1736416800000",
  "title": "Help with project planning",
  "createdAt": "2026-01-09T10:00:00.000Z",
  "updatedAt": "2026-01-09T10:05:30.000Z",
  "messages": [
    {
      "id": "msg_1736416800000_0",
      "role": "user",
      "content": "Help me plan my project milestones",
      "timestamp": "2026-01-09T10:00:00.000Z",
      "status": "sent"
    },
    {
      "id": "msg_1736416802000_1",
      "role": "assistant",
      "content": "I'd be happy to help you plan your project milestones...",
      "timestamp": "2026-01-09T10:00:02.000Z"
    }
  ]
}
```

### Stored Settings

```json
{
  "provider": "chutes",
  "apiKey": "cpk_abc123...",
  "model": "deepseek-ai/DeepSeek-V3-0324",
  "temperature": 0.7,
  "maxTokens": 1024,
  "systemPrompt": null
}
```
