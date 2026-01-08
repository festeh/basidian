import { writable } from 'svelte/store';
import type { PluginComponent } from './types';

export interface UISlotItem {
	id: string;
	pluginId: string;
	component: PluginComponent;
	props?: Record<string, unknown>;
	order?: number;
}

export interface SidebarPanel {
	id: string;
	pluginId: string;
	title: string;
	component: PluginComponent;
}

export interface SettingsTab {
	id: string;
	pluginId: string;
	title: string;
	component: PluginComponent;
}

export interface Notification {
	id: string;
	message: string;
	type: 'info' | 'success' | 'error';
}

function createUIRegistry() {
	const statusBarItems = writable<UISlotItem[]>([]);
	const editorToolbarItems = writable<UISlotItem[]>([]);
	const sidebarPanels = writable<SidebarPanel[]>([]);
	const settingsTabs = writable<SettingsTab[]>([]);
	const notifications = writable<Notification[]>([]);

	return {
		statusBarItems: { subscribe: statusBarItems.subscribe },
		editorToolbarItems: { subscribe: editorToolbarItems.subscribe },
		sidebarPanels: { subscribe: sidebarPanels.subscribe },
		settingsTabs: { subscribe: settingsTabs.subscribe },
		notifications: { subscribe: notifications.subscribe },

		registerStatusBarItem(
			pluginId: string,
			component: PluginComponent,
			props?: Record<string, unknown>
		) {
			const id = `${pluginId}-statusbar-${Date.now()}`;
			statusBarItems.update((items) => [...items, { id, pluginId, component, props }]);
			return () => {
				statusBarItems.update((items) => items.filter((i) => i.id !== id));
			};
		},

		registerEditorToolbarItem(
			pluginId: string,
			component: PluginComponent,
			props?: Record<string, unknown>
		) {
			const id = `${pluginId}-toolbar-${Date.now()}`;
			editorToolbarItems.update((items) => [...items, { id, pluginId, component, props }]);
			return () => {
				editorToolbarItems.update((items) => items.filter((i) => i.id !== id));
			};
		},

		registerSidebarPanel(
			pluginId: string,
			id: string,
			title: string,
			component: PluginComponent
		) {
			const fullId = `${pluginId}-${id}`;
			sidebarPanels.update((panels) => [...panels, { id: fullId, pluginId, title, component }]);
			return () => {
				sidebarPanels.update((panels) => panels.filter((p) => p.id !== fullId));
			};
		},

		registerSettingsTab(
			pluginId: string,
			id: string,
			title: string,
			component: PluginComponent
		) {
			const fullId = `${pluginId}-${id}`;
			settingsTabs.update((tabs) => [...tabs, { id: fullId, pluginId, title, component }]);
			return () => {
				settingsTabs.update((tabs) => tabs.filter((t) => t.id !== fullId));
			};
		},

		showNotification(message: string, type: 'info' | 'success' | 'error' = 'info') {
			const id = Date.now().toString();
			notifications.update((n) => [...n, { id, message, type }]);
			setTimeout(() => {
				notifications.update((n) => n.filter((item) => item.id !== id));
			}, 5000);
		},

		dismissNotification(id: string) {
			notifications.update((n) => n.filter((item) => item.id !== id));
		},

		clearPluginUI(pluginId: string) {
			statusBarItems.update((items) => items.filter((i) => i.pluginId !== pluginId));
			editorToolbarItems.update((items) => items.filter((i) => i.pluginId !== pluginId));
			sidebarPanels.update((panels) => panels.filter((p) => p.pluginId !== pluginId));
			settingsTabs.update((tabs) => tabs.filter((t) => t.pluginId !== pluginId));
		}
	};
}

export const uiRegistry = createUIRegistry();
