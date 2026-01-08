import { browser } from '$app/environment';
import { writable, get } from 'svelte/store';
import type { Plugin, PluginManifest, LoadedPlugin } from './types';
import type { FsNode, Theme } from '$lib/types';
import { createPluginContext } from './context';
import { uiRegistry } from './ui-registry';
import { createLogger } from '$lib/utils/logger';

const log = createLogger('PluginLoader');

// Store for loaded plugins
export const loadedPlugins = writable<Map<string, LoadedPlugin>>(new Map());

class PluginManager {
	private plugins = new Map<string, LoadedPlugin>();
	private initialized = false;

	async initialize() {
		if (this.initialized || !browser) return;
		this.initialized = true;

		log.info('Initializing plugin system');

		// Load plugins from the development plugins folder
		await this.loadDevPlugins();
	}

	private async loadDevPlugins() {
		// Use Vite's import.meta.glob for development plugins
		// Plugins are expected to be in /src/lib/plugins/installed/
		try {
			const pluginModules = import.meta.glob('./installed/*/index.ts', { eager: false });
			const manifestModules = import.meta.glob('./installed/*/manifest.json', {
				eager: true,
				import: 'default'
			});

			for (const [manifestPath, manifest] of Object.entries(manifestModules)) {
				const pluginDir = manifestPath.replace('/manifest.json', '');
				const indexPath = `${pluginDir}/index.ts`;

				if (indexPath in pluginModules) {
					try {
						await this.loadPluginFromModule(
							manifest as PluginManifest,
							pluginDir,
							pluginModules[indexPath] as () => Promise<{ default: Plugin }>
						);
					} catch (e) {
						log.error(`Failed to load plugin ${(manifest as PluginManifest).id}`, e);
					}
				}
			}
		} catch (e) {
			log.debug('No dev plugins found or error loading', e);
		}
	}

	private async loadPluginFromModule(
		manifest: PluginManifest,
		pluginPath: string,
		loader: () => Promise<{ default: Plugin }>
	) {
		log.info(`Loading plugin: ${manifest.name} v${manifest.version}`);

		// Load the plugin module
		const module = await loader();
		const instance: Plugin = module.default;

		// Create context for this plugin
		const context = createPluginContext(manifest, pluginPath);

		const loaded: LoadedPlugin = {
			manifest,
			instance,
			context,
			enabled: true
		};

		this.plugins.set(manifest.id, loaded);
		this.updateStore();

		// Call onLoad hook
		if (instance.onLoad) {
			try {
				await instance.onLoad(context);
				log.info(`Plugin ${manifest.name} loaded successfully`);
			} catch (e) {
				log.error(`Plugin ${manifest.name} onLoad failed`, e);
			}
		}
	}

	async loadPluginFromUrl(manifestUrl: string) {
		if (!browser) return;

		try {
			// Fetch manifest
			const manifestResponse = await fetch(manifestUrl);
			const manifest: PluginManifest = await manifestResponse.json();

			const pluginDir = manifestUrl.replace('/manifest.json', '');
			const moduleUrl = `${pluginDir}/${manifest.main}`;

			// Dynamic import
			const module = await import(/* @vite-ignore */ moduleUrl);
			const instance: Plugin = module.default || module;

			const context = createPluginContext(manifest, pluginDir);

			const loaded: LoadedPlugin = {
				manifest,
				instance,
				context,
				enabled: true
			};

			this.plugins.set(manifest.id, loaded);
			this.updateStore();

			if (instance.onLoad) {
				await instance.onLoad(context);
			}

			log.info(`Loaded plugin from URL: ${manifest.name}`);
		} catch (e) {
			log.error(`Failed to load plugin from ${manifestUrl}`, e);
		}
	}

	async unloadPlugin(pluginId: string) {
		const plugin = this.plugins.get(pluginId);
		if (!plugin) return;

		log.info(`Unloading plugin: ${plugin.manifest.name}`);

		// Call onUnload hook
		if (plugin.instance.onUnload) {
			try {
				await plugin.instance.onUnload(plugin.context);
			} catch (e) {
				log.error(`Plugin ${plugin.manifest.name} onUnload failed`, e);
			}
		}

		// Clear plugin UI
		uiRegistry.clearPluginUI(pluginId);

		this.plugins.delete(pluginId);
		this.updateStore();
	}

	async enablePlugin(pluginId: string) {
		const plugin = this.plugins.get(pluginId);
		if (!plugin || plugin.enabled) return;

		plugin.enabled = true;
		if (plugin.instance.onLoad) {
			await plugin.instance.onLoad(plugin.context);
		}
		this.updateStore();
	}

	async disablePlugin(pluginId: string) {
		const plugin = this.plugins.get(pluginId);
		if (!plugin || !plugin.enabled) return;

		plugin.enabled = false;
		if (plugin.instance.onUnload) {
			await plugin.instance.onUnload(plugin.context);
		}
		uiRegistry.clearPluginUI(pluginId);
		this.updateStore();
	}

	private updateStore() {
		loadedPlugins.set(new Map(this.plugins));
	}

	// Hook dispatchers
	async dispatchFileOpen(file: FsNode) {
		for (const plugin of this.plugins.values()) {
			if (plugin.enabled && plugin.instance.onFileOpen) {
				try {
					await plugin.instance.onFileOpen(file, plugin.context);
				} catch (e) {
					log.error(`Plugin ${plugin.manifest.id} onFileOpen error`, e);
				}
			}
		}
	}

	async dispatchFileSave(file: FsNode) {
		for (const plugin of this.plugins.values()) {
			if (plugin.enabled && plugin.instance.onFileSave) {
				try {
					await plugin.instance.onFileSave(file, plugin.context);
				} catch (e) {
					log.error(`Plugin ${plugin.manifest.id} onFileSave error`, e);
				}
			}
		}
	}

	async dispatchFileCreate(file: FsNode) {
		for (const plugin of this.plugins.values()) {
			if (plugin.enabled && plugin.instance.onFileCreate) {
				try {
					await plugin.instance.onFileCreate(file, plugin.context);
				} catch (e) {
					log.error(`Plugin ${plugin.manifest.id} onFileCreate error`, e);
				}
			}
		}
	}

	async dispatchFileDelete(file: FsNode) {
		for (const plugin of this.plugins.values()) {
			if (plugin.enabled && plugin.instance.onFileDelete) {
				try {
					await plugin.instance.onFileDelete(file, plugin.context);
				} catch (e) {
					log.error(`Plugin ${plugin.manifest.id} onFileDelete error`, e);
				}
			}
		}
	}

	async dispatchThemeChange(theme: Theme) {
		for (const plugin of this.plugins.values()) {
			if (plugin.enabled && plugin.instance.onThemeChange) {
				try {
					await plugin.instance.onThemeChange(theme, plugin.context);
				} catch (e) {
					log.error(`Plugin ${plugin.manifest.id} onThemeChange error`, e);
				}
			}
		}
	}

	getPlugin(pluginId: string): LoadedPlugin | undefined {
		return this.plugins.get(pluginId);
	}

	getAllPlugins(): LoadedPlugin[] {
		return Array.from(this.plugins.values());
	}
}

export const pluginManager = new PluginManager();
