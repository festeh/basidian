/**
 * AI Chat Plugin
 *
 * Provides an AI chat interface in a right-side panel.
 * Registers a sidebar action button and settings tab.
 */

import type { Plugin, PluginContext } from '$lib/plugins/types';
import { initStorage } from './storage';
import ChatButton from './ChatButton.svelte';
import Settings from './Settings.svelte';
import { writable, type Writable } from 'svelte/store';

// Shared state for chat pane visibility
export const chatPaneOpen: Writable<boolean> = writable(false);

// Plugin context reference
let ctx: PluginContext | null = null;

// Unregister functions for cleanup
let unregisterSidebarAction: (() => void) | null = null;
let unregisterSettingsTab: (() => void) | null = null;

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

/**
 * Get the plugin context.
 */
export function getContext(): PluginContext | null {
  return ctx;
}

const plugin: Plugin = {
  async onLoad(context: PluginContext) {
    ctx = context;
    ctx.log.info('AI Chat plugin loading...');

    // Initialize storage with plugin's storage API
    initStorage(ctx.storage);

    // Register sidebar action button (appears below search bar)
    unregisterSidebarAction = ctx.ui.registerSidebarAction(ChatButton);

    // Register settings tab
    unregisterSettingsTab = ctx.ui.registerSettingsTab(
      'ai-chat',
      'AI Chat',
      Settings
    );

    ctx.log.info('AI Chat plugin loaded!');
  },

  async onUnload(context: PluginContext) {
    context.log.info('AI Chat plugin unloading...');

    // Close chat pane if open
    closeChatPane();

    // Unregister UI components
    unregisterSidebarAction?.();
    unregisterSettingsTab?.();

    // Clear references
    unregisterSidebarAction = null;
    unregisterSettingsTab = null;
    ctx = null;

    context.log.info('AI Chat plugin unloaded!');
  },
};

export default plugin;
