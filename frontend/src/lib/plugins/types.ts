import type { Component } from 'svelte';
import type { Writable, Readable } from 'svelte/store';
import type { FsNode, Theme, ThemeName, Settings } from '$lib/types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type PluginComponent = Component<any, any, any>;

export interface PluginManifest {
	id: string;
	name: string;
	version: string;
	description?: string;
	author?: string;
	main: string;
	hooks?: string[];
	commands?: PluginCommand[];
	contextMenus?: PluginContextMenu[];
}

export interface PluginCommand {
	id: string;
	name: string;
	shortcut?: string;
	callback?: () => void | Promise<void>;
}

export interface PluginContextMenu {
	id: string;
	label: string;
	context: 'fileTree' | 'editor' | 'sidebar';
	callback?: (target: FsNode | null) => void;
}

export interface ThemeStore {
	subscribe: (run: (value: ThemeName) => void) => () => void;
	set: (value: ThemeName) => void;
}

export interface PluginStores {
	filesystem: {
		rootNodes: Writable<FsNode[]>;
		currentFile: Writable<FsNode | null>;
		selectedNode: Writable<FsNode | null>;
		isLoading: Writable<boolean>;
		isLoadingFile: Writable<boolean>;
		error: Writable<string | null>;
	};
	settings: Writable<Settings>;
	theme: {
		currentThemeName: ThemeStore;
		currentTheme: Readable<Theme>;
	};
}

export interface PluginActions {
	filesystem: {
		loadTree: () => Promise<void>;
		toggleFolder: (node: FsNode) => void;
		selectNode: (node: FsNode | null) => void;
		openFile: (node: FsNode) => Promise<void>;
		closeFile: () => void;
		createFile: (parentPath: string, name: string, content?: string) => Promise<FsNode | null>;
		createFolder: (parentPath: string, name: string) => Promise<FsNode | null>;
		updateNode: (node: FsNode) => Promise<FsNode | null>;
		deleteNode: (node: FsNode) => Promise<void>;
		renameNode: (node: FsNode, newName: string) => Promise<void>;
		searchFiles: (query: string) => Promise<FsNode[]>;
	};
	theme: {
		setTheme: (name: ThemeName) => void;
		applyTheme: (theme: Theme) => void;
	};
}

export interface PluginUI {
	registerStatusBarItem: (
		component: PluginComponent,
		props?: Record<string, unknown>
	) => () => void;
	registerSidebarPanel: (
		id: string,
		title: string,
		component: PluginComponent
	) => () => void;
	registerSidebarAction: (
		component: PluginComponent,
		props?: Record<string, unknown>,
		order?: number
	) => () => void;
	registerSettingsTab: (
		id: string,
		title: string,
		component: PluginComponent
	) => () => void;
	registerEditorToolbarItem: (
		component: PluginComponent,
		props?: Record<string, unknown>
	) => () => void;
	showNotification: (message: string, type?: 'info' | 'success' | 'error') => void;
}

export interface PluginCommands {
	register: (command: PluginCommand) => () => void;
	execute: (commandId: string) => Promise<void>;
	getAll: () => PluginCommand[];
}

export interface PluginContextMenuAPI {
	register: (menu: PluginContextMenu) => () => void;
	getItems: (context: 'fileTree' | 'editor' | 'sidebar') => PluginContextMenu[];
}

export interface PluginStorage {
	get: <T>(key: string) => T | null;
	set: <T>(key: string, value: T) => void;
	remove: (key: string) => void;
}

export interface PluginLogger {
	debug: (message: string, ...args: unknown[]) => void;
	info: (message: string, ...args: unknown[]) => void;
	warn: (message: string, ...args: unknown[]) => void;
	error: (message: string, ...args: unknown[]) => void;
}

export interface PluginContext {
	manifest: PluginManifest;
	pluginPath: string;
	stores: PluginStores;
	actions: PluginActions;
	ui: PluginUI;
	commands: PluginCommands;
	contextMenu: PluginContextMenuAPI;
	storage: PluginStorage;
	log: PluginLogger;
}

export interface Plugin {
	onLoad?: (ctx: PluginContext) => void | Promise<void>;
	onUnload?: (ctx: PluginContext) => void | Promise<void>;
	onFileOpen?: (file: FsNode, ctx: PluginContext) => void | Promise<void>;
	onFileSave?: (file: FsNode, ctx: PluginContext) => void | Promise<void>;
	onFileCreate?: (file: FsNode, ctx: PluginContext) => void | Promise<void>;
	onFileDelete?: (file: FsNode, ctx: PluginContext) => void | Promise<void>;
	onThemeChange?: (theme: Theme, ctx: PluginContext) => void | Promise<void>;
}

export interface LoadedPlugin {
	manifest: PluginManifest;
	instance: Plugin;
	context: PluginContext;
	enabled: boolean;
}
