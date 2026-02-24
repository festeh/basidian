/**
 * AI Chat Plugin - TypeScript Interfaces
 */

// =============================================================================
// Core Entities
// =============================================================================

/**
 * A conversation between the user and AI assistant.
 */
export interface Conversation {
  /** Unique identifier (format: conv_{timestamp}) */
  id: string;
  /** Optional display title, auto-generated from first message if null */
  title: string | null;
  /** ISO 8601 timestamp when conversation was created */
  createdAt: string;
  /** ISO 8601 timestamp when conversation was last updated */
  updatedAt: string;
  /** Ordered list of messages in the conversation */
  messages: Message[];
}

/**
 * A single message in a conversation.
 */
export interface Message {
  /** Unique identifier (format: msg_{timestamp}_{index}) */
  id: string;
  /** Who sent this message */
  role: MessageRole;
  /** The text content of the message */
  content: string;
  /** ISO 8601 timestamp when message was created */
  timestamp: string;
  /** Delivery status for user messages */
  status?: MessageStatus;
  /** Error details if status is 'error' */
  error?: string;
}

export type MessageRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'sending' | 'sent' | 'error';

// =============================================================================
// Settings & Configuration
// =============================================================================

/**
 * User configuration for AI chat.
 */
export interface AISettings {
  /** Selected AI provider ID */
  provider: string;
  /** Provider API key (stored locally) */
  apiKey: string | null;
  /** Model identifier for the selected provider */
  model: string;
  /** Response randomness (0.0-2.0) */
  temperature: number;
  /** Maximum response length in tokens */
  maxTokens: number;
  /** Optional custom system prompt */
  systemPrompt: string | null;
}

/**
 * Default settings for new installations.
 */
export const DEFAULT_SETTINGS: AISettings = {
  provider: 'chutes',
  apiKey: null,
  model: 'deepseek-ai/DeepSeek-V3-0324',
  temperature: 0.7,
  maxTokens: 1024,
  systemPrompt: null,
};

/**
 * Configuration for an AI provider.
 */
export interface ProviderConfig {
  /** Unique provider identifier */
  id: string;
  /** Display name */
  name: string;
  /** API base URL */
  baseUrl: string;
  /** Available model identifiers */
  models: string[];
  /** Default model for this provider */
  defaultModel: string;
}

// =============================================================================
// Provider Interface
// =============================================================================

/**
 * Options for sending a message to the AI.
 */
export interface SendMessageOptions {
  /** Provider API key */
  apiKey: string;
  /** Model identifier */
  model: string;
  /** Response randomness */
  temperature?: number;
  /** Maximum response tokens */
  maxTokens?: number;
  /** Enable streaming response */
  stream?: boolean;
}

/**
 * Interface that all AI providers must implement.
 */
export interface AIProvider {
  /** Unique provider identifier */
  id: string;
  /** Display name */
  name: string;
  /** Provider configuration */
  config: ProviderConfig;

  /**
   * Send messages to the AI and get a response.
   * @param messages - Conversation history to send
   * @param options - Request options
   * @param onChunk - Callback for streaming chunks (optional)
   * @returns The complete assistant response
   */
  sendMessage(
    messages: Message[],
    options: SendMessageOptions,
    onChunk?: (chunk: string) => void
  ): Promise<string>;

  /**
   * Validate that an API key is valid for this provider.
   * @param apiKey - The API key to validate
   * @returns True if valid, false otherwise
   */
  validateApiKey(apiKey: string): Promise<boolean>;
}

// =============================================================================
// API Request/Response Types (OpenAI-compatible)
// =============================================================================

/**
 * Chat completion request body (OpenAI-compatible format).
 */
export interface ChatCompletionRequest {
  model: string;
  messages: Array<{
    role: MessageRole;
    content: string;
  }>;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

/**
 * Chat completion response (non-streaming).
 */
export interface ChatCompletionResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: 'assistant';
      content: string;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * Streaming chunk (Server-Sent Events format).
 */
export interface ChatCompletionChunk {
  id: string;
  object: 'chat.completion.chunk';
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: 'assistant';
      content?: string;
    };
    finish_reason: string | null;
  }>;
}

// =============================================================================
// Storage Keys
// =============================================================================

/**
 * Keys used for localStorage.
 * All keys are prefixed with 'basidian-ai-chat-'.
 */
export const STORAGE_KEYS = {
  SETTINGS: 'settings',
  CONVERSATIONS: 'conversations',
  CURRENT_CONVERSATION_ID: 'currentConversationId',
} as const;

// =============================================================================
// Provider Registry
// =============================================================================

/**
 * Built-in provider configurations.
 */
export const PROVIDERS: Record<string, ProviderConfig> = {
  chutes: {
    id: 'chutes',
    name: 'Chutes AI',
    baseUrl: 'https://llm.chutes.ai/v1',
    models: [
      'deepseek-ai/DeepSeek-V3-0324',
      'moonshotai/Kimi-K2-Instruct-0905',
      'Qwen/Qwen3-235B-A22B',
    ],
    defaultModel: 'deepseek-ai/DeepSeek-V3-0324',
  },
};
