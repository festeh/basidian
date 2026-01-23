/**
 * AI Chat Plugin - Storage Helpers
 *
 * Provides functions for persisting conversations and settings
 * using the plugin storage API (localStorage).
 */

import type { PluginStorage } from '$lib/plugins/types';
import {
  type Conversation,
  type AISettings,
  DEFAULT_SETTINGS,
  STORAGE_KEYS,
} from './types';

let storage: PluginStorage | null = null;

/**
 * Initialize the storage module with the plugin's storage API.
 */
export function initStorage(pluginStorage: PluginStorage): void {
  storage = pluginStorage;
}

/**
 * Get storage instance, throws if not initialized.
 */
function getStorage(): PluginStorage {
  if (!storage) {
    throw new Error('Storage not initialized. Call initStorage first.');
  }
  return storage;
}

// =============================================================================
// Settings
// =============================================================================

/**
 * Get the current AI settings, or defaults if none saved.
 */
export function getSettings(): AISettings {
  const stored = getStorage().get<AISettings>(STORAGE_KEYS.SETTINGS);
  return stored ?? { ...DEFAULT_SETTINGS };
}

/**
 * Save AI settings to storage.
 */
export function saveSettings(settings: AISettings): void {
  getStorage().set(STORAGE_KEYS.SETTINGS, settings);
}

// =============================================================================
// Conversations
// =============================================================================

/**
 * Get all saved conversations, sorted by updatedAt (newest first).
 */
export function getConversations(): Conversation[] {
  const stored = getStorage().get<Conversation[]>(STORAGE_KEYS.CONVERSATIONS);
  const conversations = stored ?? [];
  return conversations.sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );
}

/**
 * Get a specific conversation by ID.
 */
export function getConversation(id: string): Conversation | null {
  const conversations = getConversations();
  return conversations.find((c) => c.id === id) ?? null;
}

/**
 * Save a conversation (creates new or updates existing).
 */
export function saveConversation(conversation: Conversation): void {
  const conversations = getConversations();
  const index = conversations.findIndex((c) => c.id === conversation.id);

  if (index >= 0) {
    conversations[index] = conversation;
  } else {
    conversations.push(conversation);
  }

  getStorage().set(STORAGE_KEYS.CONVERSATIONS, conversations);
}

/**
 * Delete a conversation by ID.
 */
export function deleteConversation(id: string): void {
  const conversations = getConversations();
  const filtered = conversations.filter((c) => c.id !== id);
  getStorage().set(STORAGE_KEYS.CONVERSATIONS, filtered);

  // Clear current conversation if it was deleted
  const currentId = getCurrentConversationId();
  if (currentId === id) {
    setCurrentConversationId(null);
  }
}

// =============================================================================
// Current Conversation
// =============================================================================

/**
 * Get the ID of the currently active conversation.
 */
export function getCurrentConversationId(): string | null {
  return getStorage().get<string>(STORAGE_KEYS.CURRENT_CONVERSATION_ID);
}

/**
 * Set the currently active conversation ID.
 */
export function setCurrentConversationId(id: string | null): void {
  if (id === null) {
    getStorage().remove(STORAGE_KEYS.CURRENT_CONVERSATION_ID);
  } else {
    getStorage().set(STORAGE_KEYS.CURRENT_CONVERSATION_ID, id);
  }
}

// =============================================================================
// Helpers
// =============================================================================

/**
 * Create a new conversation with a unique ID.
 */
export function createConversation(): Conversation {
  const now = new Date().toISOString();
  return {
    id: `conv_${Date.now()}`,
    title: null,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

/**
 * Generate a unique message ID.
 */
export function createMessageId(index: number): string {
  return `msg_${Date.now()}_${index}`;
}

/**
 * Auto-generate a conversation title from the first user message.
 */
export function generateTitle(content: string): string {
  const maxLength = 50;
  const trimmed = content.trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  return trimmed.substring(0, maxLength - 3) + '...';
}
