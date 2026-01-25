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
import { setContext, closeChatPane } from './state';

// Re-export state for external consumers
export { chatPaneOpen, toggleChatPane, openChatPane, closeChatPane, getContext } from './state';

// Unregister functions for cleanup
let unregisterSidebarAction: (() => void) | null = null;
let unregisterSettingsTab: (() => void) | null = null;

const plugin: Plugin = {
	async onLoad(context: PluginContext) {
		setContext(context);
		context.log.info('AI Chat plugin loading...');

		// Initialize storage with plugin's storage API
		initStorage(context.storage);

		// Register sidebar action button (appears below search bar)
		unregisterSidebarAction = context.ui.registerSidebarAction(ChatButton);

		// Register settings tab
		unregisterSettingsTab = context.ui.registerSettingsTab(
			'ai-chat',
			'AI Chat',
			Settings
		);

		context.log.info('AI Chat plugin loaded!');
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
		setContext(null);

		context.log.info('AI Chat plugin unloaded!');
	},
};

export default plugin;
