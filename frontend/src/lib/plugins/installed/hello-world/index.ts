import type { Plugin, PluginContext } from '../../types';
import WordCount from './WordCount.svelte';

let unregisterStatusBar: (() => void) | null = null;

const plugin: Plugin = {
	async onLoad(ctx: PluginContext) {
		ctx.log.info('Hello World plugin loaded!');

		// Register a status bar component
		unregisterStatusBar = ctx.ui.registerStatusBarItem(WordCount);

		// Show a welcome notification
		ctx.ui.showNotification('Hello World plugin active!', 'success');
	},

	async onUnload(ctx: PluginContext) {
		ctx.log.info('Hello World plugin unloading...');

		// Cleanup
		unregisterStatusBar?.();
	},

	async onFileOpen(file, ctx) {
		ctx.log.debug(`File opened: ${file.name}`);

		// Store the word count
		const wordCount = (file.content || '').split(/\s+/).filter(Boolean).length;
		ctx.storage.set('lastWordCount', wordCount);
	},

	async onFileSave(file, ctx) {
		ctx.log.debug(`File saved: ${file.name}`);
	}
};

export default plugin;
