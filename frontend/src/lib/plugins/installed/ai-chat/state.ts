/**
 * AI Chat Plugin - Shared State
 * Separated to avoid circular imports with Svelte components
 */

import type { PluginContext } from '$lib/plugins/types';
import { writable, type Writable } from 'svelte/store';

// Shared state for chat pane visibility
export const chatPaneOpen: Writable<boolean> = writable(false);

// Plugin context reference
let ctx: PluginContext | null = null;

/**
 * Set the plugin context (called from index.ts onLoad)
 */
export function setContext(context: PluginContext | null): void {
	ctx = context;
}

/**
 * Get the plugin context.
 */
export function getContext(): PluginContext | null {
	return ctx;
}

/**
 * Toggle the chat pane open/closed.
 */
export function toggleChatPane(): void {
	chatPaneOpen.update((open) => !open);
}

/**
 * Open the chat pane.
 */
export function openChatPane(): void {
	chatPaneOpen.set(true);
}

/**
 * Close the chat pane.
 */
export function closeChatPane(): void {
	chatPaneOpen.set(false);
}
