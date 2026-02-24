import { browser } from '$app/environment';
import type {
	PluginManifest,
	PluginContext,
	PluginCommand,
	PluginContextMenu,
	PluginComponent
} from './types';
import { uiRegistry } from './ui-registry';
import {
	rootNodes,
	currentFile,
	selectedNode,
	isLoading,
	isLoadingFile,
	error,
	filesystemActions
} from '$lib/stores/filesystem';
import { settings } from '$lib/stores/settings';
import { currentThemeName, currentTheme, applyTheme } from '$lib/stores/theme';
import { createLogger } from '$lib/utils/logger';
import type { ThemeName, Theme } from '$lib/types';

// Command registry (shared across all plugins)
const commands = new Map<string, PluginCommand>();

// Context menu registry
const contextMenuItems = new Map<string, PluginContextMenu>();

export function createPluginContext(
	manifest: PluginManifest,
	pluginPath: string
): PluginContext {
	const log = createLogger(`Plugin:${manifest.id}`);
	const storagePrefix = `basidian-plugin-${manifest.id}-`;

	const context: PluginContext = {
		manifest,
		pluginPath,

		stores: {
			filesystem: {
				rootNodes,
				currentFile,
				selectedNode,
				isLoading,
				isLoadingFile,
				error
			},
			settings,
			theme: {
				currentThemeName,
				currentTheme
			}
		},

		actions: {
			filesystem: {
				loadTree: () => filesystemActions.loadTree(),
				toggleFolder: (node) => filesystemActions.toggleFolder(node),
				selectNode: (node) => filesystemActions.selectNode(node),
				openFile: (node) => filesystemActions.openFile(node),
				closeFile: () => filesystemActions.closeFile(),
				createFile: (parentPath, name, content) =>
					filesystemActions.createFile(parentPath, name, content),
				createFolder: (parentPath, name) => filesystemActions.createFolder(parentPath, name),
				updateNode: (node) => filesystemActions.updateNode(node),
				deleteNode: (node) => filesystemActions.deleteNode(node),
				renameNode: (node, newName) => filesystemActions.renameNode(node, newName),
				searchFiles: (query) => filesystemActions.searchFiles(query)
			},
			theme: {
				setTheme: (name: ThemeName) => currentThemeName.set(name),
				applyTheme: (theme: Theme) => applyTheme(theme)
			}
		},

		ui: {
			registerStatusBarItem: (component: PluginComponent, props?: Record<string, unknown>) =>
				uiRegistry.registerStatusBarItem(manifest.id, component, props),
			registerSidebarPanel: (id: string, title: string, component: PluginComponent) =>
				uiRegistry.registerSidebarPanel(manifest.id, id, title, component),
			registerSidebarAction: (
				component: PluginComponent,
				props?: Record<string, unknown>,
				order?: number
			) => uiRegistry.registerSidebarAction(manifest.id, component, props, order),
			registerSettingsTab: (id: string, title: string, component: PluginComponent) =>
				uiRegistry.registerSettingsTab(manifest.id, id, title, component),
			registerEditorToolbarItem: (component: PluginComponent, props?: Record<string, unknown>) =>
				uiRegistry.registerEditorToolbarItem(manifest.id, component, props),
			showNotification: (message: string, type?: 'info' | 'success' | 'error') =>
				uiRegistry.showNotification(message, type)
		},

		commands: {
			register: (command: PluginCommand) => {
				const fullId = `${manifest.id}.${command.id}`;
				const registeredCommand = { ...command, id: fullId };
				commands.set(fullId, registeredCommand);
				return () => {
					commands.delete(fullId);
				};
			},
			execute: async (commandId: string) => {
				const command = commands.get(commandId);
				if (command?.callback) {
					await command.callback();
				}
			},
			getAll: () => Array.from(commands.values())
		},

		contextMenu: {
			register: (menu: PluginContextMenu) => {
				const fullId = `${manifest.id}.${menu.id}`;
				const registeredMenu = { ...menu, id: fullId };
				contextMenuItems.set(fullId, registeredMenu);
				return () => {
					contextMenuItems.delete(fullId);
				};
			},
			getItems: (context: 'fileTree' | 'editor' | 'sidebar') =>
				Array.from(contextMenuItems.values()).filter((m) => m.context === context)
		},

		storage: {
			get: <T>(key: string): T | null => {
				if (!browser) return null;
				try {
					const stored = localStorage.getItem(storagePrefix + key);
					return stored ? JSON.parse(stored) : null;
				} catch {
					return null;
				}
			},
			set: <T>(key: string, value: T) => {
				if (!browser) return;
				localStorage.setItem(storagePrefix + key, JSON.stringify(value));
			},
			remove: (key: string) => {
				if (!browser) return;
				localStorage.removeItem(storagePrefix + key);
			}
		},

		log
	};

	return context;
}

// Export for global access to commands and context menus
export function getCommands(): PluginCommand[] {
	return Array.from(commands.values());
}

export function getContextMenuItems(context: 'fileTree' | 'editor' | 'sidebar'): PluginContextMenu[] {
	return Array.from(contextMenuItems.values()).filter((m) => m.context === context);
}

export async function executeCommand(commandId: string): Promise<void> {
	const command = commands.get(commandId);
	if (command?.callback) {
		await command.callback();
	}
}
