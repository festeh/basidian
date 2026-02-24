/**
 * AI Chat - Storage Helpers
 *
 * Persists conversations and settings using localStorage.
 */

import {
  type Conversation,
  type AISettings,
  DEFAULT_SETTINGS,
  STORAGE_KEYS,
} from './types';

const STORAGE_PREFIX = 'basidian-ai-chat-';

function storageGet<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function storageSet<T>(key: string, value: T): void {
  localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
}

function storageRemove(key: string): void {
  localStorage.removeItem(STORAGE_PREFIX + key);
}

// =============================================================================
// Settings
// =============================================================================

export function getSettings(): AISettings {
  const stored = storageGet<AISettings>(STORAGE_KEYS.SETTINGS);
  return stored ?? { ...DEFAULT_SETTINGS };
}

export function saveSettings(settings: AISettings): void {
  storageSet(STORAGE_KEYS.SETTINGS, settings);
}

// =============================================================================
// Conversations
// =============================================================================

export function getConversations(): Conversation[] {
  const stored = storageGet<Conversation[]>(STORAGE_KEYS.CONVERSATIONS);
  const conversations = stored ?? [];
  return conversations.sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  );
}

export function getConversation(id: string): Conversation | null {
  const conversations = getConversations();
  return conversations.find((c) => c.id === id) ?? null;
}

export function saveConversation(conversation: Conversation): void {
  const conversations = getConversations();
  const index = conversations.findIndex((c) => c.id === conversation.id);

  if (index >= 0) {
    conversations[index] = conversation;
  } else {
    conversations.push(conversation);
  }

  storageSet(STORAGE_KEYS.CONVERSATIONS, conversations);
}

export function deleteConversation(id: string): void {
  const conversations = getConversations();
  const filtered = conversations.filter((c) => c.id !== id);
  storageSet(STORAGE_KEYS.CONVERSATIONS, filtered);

  const currentId = getCurrentConversationId();
  if (currentId === id) {
    setCurrentConversationId(null);
  }
}

// =============================================================================
// Current Conversation
// =============================================================================

export function getCurrentConversationId(): string | null {
  return storageGet<string>(STORAGE_KEYS.CURRENT_CONVERSATION_ID);
}

export function setCurrentConversationId(id: string | null): void {
  if (id === null) {
    storageRemove(STORAGE_KEYS.CURRENT_CONVERSATION_ID);
  } else {
    storageSet(STORAGE_KEYS.CURRENT_CONVERSATION_ID, id);
  }
}

// =============================================================================
// Helpers
// =============================================================================

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

export function createMessageId(index: number): string {
  return `msg_${Date.now()}_${index}`;
}

export function generateTitle(content: string): string {
  const maxLength = 50;
  const trimmed = content.trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  return trimmed.substring(0, maxLength - 3) + '...';
}
