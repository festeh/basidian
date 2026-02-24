/**
 * AI Chat - Shared State
 */

import { writable, type Writable } from 'svelte/store';

export const chatPaneOpen: Writable<boolean> = writable(false);

export function toggleChatPane(): void {
	chatPaneOpen.update((open) => !open);
}

export function openChatPane(): void {
	chatPaneOpen.set(true);
}

export function closeChatPane(): void {
	chatPaneOpen.set(false);
}
