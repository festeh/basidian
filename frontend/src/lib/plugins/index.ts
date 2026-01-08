// Types
export type {
	Plugin,
	PluginManifest,
	PluginContext,
	PluginCommand,
	PluginContextMenu,
	LoadedPlugin,
	PluginStores,
	PluginActions,
	PluginUI,
	PluginDOM,
	PluginStorage,
	PluginLogger
} from './types';

// Plugin Manager
export { pluginManager, loadedPlugins } from './loader';

// UI Registry
export { uiRegistry } from './ui-registry';
export type { UISlotItem, SidebarPanel, SettingsTab, Notification } from './ui-registry';

// Context utilities
export { getCommands, getContextMenuItems, executeCommand } from './context';
