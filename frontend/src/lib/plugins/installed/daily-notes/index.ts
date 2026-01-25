import type { Plugin, PluginContext } from '../../types';
import DailyNoteButton from './DailyNoteButton.svelte';
import { setContext } from './state';

// Re-export state for external consumers
export {
	type DailyNotesSettings,
	getSettings,
	saveSettings,
	formatDate,
	parseDate,
	getDailyPath,
	openOrCreateDaily,
	getDailyNotesForMonth,
	todayExists
} from './state';

let unregisterSidebarAction: (() => void) | null = null;

const plugin: Plugin = {
	async onLoad(context: PluginContext) {
		setContext(context);
		context.log.info('Daily Notes plugin loaded!');

		// Register sidebar action button (includes calendar popup)
		unregisterSidebarAction = context.ui.registerSidebarAction(DailyNoteButton);
	},

	async onUnload(context: PluginContext) {
		context.log.info('Daily Notes plugin unloading...');
		unregisterSidebarAction?.();
		setContext(null);
	}
};

export default plugin;
