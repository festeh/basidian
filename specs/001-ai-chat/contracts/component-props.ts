/**
 * AI Chat Plugin - Component Props Interfaces
 *
 * Defines the props interfaces for all Svelte components in the plugin.
 */

import type { Conversation, Message, AISettings, ProviderConfig } from './types';

// =============================================================================
// ChatButton.svelte
// =============================================================================

/**
 * Props for the sidebar action button component.
 * Registered via ctx.ui.registerSidebarAction().
 */
export interface ChatButtonProps {
  // No props required - uses internal state
}

// =============================================================================
// ChatPane.svelte
// =============================================================================

/**
 * Props for the main chat pane component.
 */
export interface ChatPaneProps {
  /** Whether the pane is visible */
  isOpen: boolean;
  /** Callback when pane should close */
  onClose: () => void;
}

// =============================================================================
// ChatMessage.svelte
// =============================================================================

/**
 * Props for individual message display.
 */
export interface ChatMessageProps {
  /** The message to display */
  message: Message;
  /** Whether this message is currently streaming */
  isStreaming?: boolean;
}

// =============================================================================
// ConversationList.svelte
// =============================================================================

/**
 * Props for conversation list/selector.
 */
export interface ConversationListProps {
  /** All conversations to display */
  conversations: Conversation[];
  /** Currently selected conversation ID */
  currentId: string | null;
  /** Callback when a conversation is selected */
  onSelect: (id: string) => void;
  /** Callback when a conversation should be deleted */
  onDelete: (id: string) => void;
  /** Callback to create a new conversation */
  onNew: () => void;
}

// =============================================================================
// Settings.svelte
// =============================================================================

/**
 * Props for the settings tab component.
 * Registered via ctx.ui.registerSettingsTab().
 */
export interface SettingsProps {
  // No props required - uses ctx.storage
}

// =============================================================================
// MessageInput.svelte
// =============================================================================

/**
 * Props for the message input component.
 */
export interface MessageInputProps {
  /** Current input value */
  value: string;
  /** Callback when input changes */
  onInput: (value: string) => void;
  /** Callback when message should be sent */
  onSend: () => void;
  /** Whether sending is disabled */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
}

// =============================================================================
// ProviderSelect.svelte
// =============================================================================

/**
 * Props for provider selection dropdown.
 */
export interface ProviderSelectProps {
  /** Available providers */
  providers: ProviderConfig[];
  /** Currently selected provider ID */
  selectedId: string;
  /** Callback when selection changes */
  onSelect: (providerId: string) => void;
}

// =============================================================================
// ModelSelect.svelte
// =============================================================================

/**
 * Props for model selection dropdown.
 */
export interface ModelSelectProps {
  /** Available models */
  models: string[];
  /** Currently selected model */
  selectedModel: string;
  /** Callback when selection changes */
  onSelect: (model: string) => void;
}

// =============================================================================
// ApiKeyInput.svelte
// =============================================================================

/**
 * Props for API key input with validation.
 */
export interface ApiKeyInputProps {
  /** Current API key value */
  value: string | null;
  /** Callback when value changes */
  onChange: (value: string) => void;
  /** Whether validation is in progress */
  isValidating?: boolean;
  /** Validation result */
  validationStatus?: 'valid' | 'invalid' | null;
  /** Callback to trigger validation */
  onValidate?: () => void;
}

// =============================================================================
// ErrorMessage.svelte
// =============================================================================

/**
 * Props for error message display.
 */
export interface ErrorMessageProps {
  /** Error message text */
  message: string;
  /** Callback for retry action */
  onRetry?: () => void;
  /** Callback to dismiss error */
  onDismiss?: () => void;
}

// =============================================================================
// LoadingIndicator.svelte
// =============================================================================

/**
 * Props for loading indicator.
 */
export interface LoadingIndicatorProps {
  /** Loading message to display */
  message?: string;
}
