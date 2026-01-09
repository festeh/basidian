<script lang="ts">
	import { goto } from '$app/navigation';
	import { currentThemeName } from '$lib/stores/theme';
	import { settings } from '$lib/stores/settings';
	import { themeList } from '$lib/themes';
	import { loadedPlugins, pluginManager, uiRegistry, type SettingsTab } from '$lib/plugins';
	import type { ThemeName } from '$lib/types';
	import type { LoadedPlugin } from '$lib/plugins';

	function selectTheme(name: ThemeName) {
		currentThemeName.set(name);
	}

	function toggleVimMode() {
		settings.update((s) => ({ ...s, vimMode: !s.vimMode }));
	}

	function goBack() {
		goto('/');
	}

	let plugins: LoadedPlugin[] = $state([]);
	loadedPlugins.subscribe((map) => {
		plugins = Array.from(map.values());
	});

	let settingsTabs: SettingsTab[] = $state([]);
	uiRegistry.settingsTabs.subscribe((tabs) => (settingsTabs = tabs));

	async function togglePlugin(pluginId: string, enabled: boolean) {
		if (enabled) {
			await pluginManager.disablePlugin(pluginId);
		} else {
			await pluginManager.enablePlugin(pluginId);
		}
	}
</script>

<div class="settings">
	<header>
		<button class="back-btn" onclick={goBack} aria-label="Go back">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
			</svg>
		</button>
		<h1>Settings</h1>
	</header>

	<main>
		<section>
			<h2>Appearance</h2>
			<div class="theme-grid">
				{#each themeList as theme}
					<button
						class="theme-card"
						class:selected={$currentThemeName === theme.name}
						onclick={() => selectTheme(theme.name as ThemeName)}
					>
						<div class="preview-colors">
							<div class="color" style="background-color: {theme.colors.base}"></div>
							<div class="color" style="background-color: {theme.colors.accent}"></div>
							<div class="color" style="background-color: {theme.colors.secondary}"></div>
						</div>
						<div class="theme-info">
							<span class="theme-name">{theme.displayName}</span>
							<span class="theme-type">{theme.isDark ? 'Dark' : 'Light'}</span>
						</div>
						{#if $currentThemeName === theme.name}
							<svg class="check" width="24" height="24" viewBox="0 0 24 24" fill="var(--color-accent)"
								>
								<path
									d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
								/>
							</svg>
						{/if}
					</button>
				{/each}
			</div>
		</section>

		<section>
			<h2>Editor</h2>
			<button class="setting-row" onclick={toggleVimMode}>
				<div class="setting-info">
					<span class="setting-name">Vim Mode</span>
					<span class="setting-desc">Use vim keybindings in the editor</span>
				</div>
				<div class="toggle" class:active={$settings.vimMode}>
					<div class="toggle-knob"></div>
				</div>
			</button>
		</section>

		{#if plugins.length > 0}
			<section>
				<h2>Plugins</h2>
				<div class="plugin-list">
					{#each plugins as plugin (plugin.manifest.id)}
						<button
							class="setting-row"
							onclick={() => togglePlugin(plugin.manifest.id, plugin.enabled)}
						>
							<div class="setting-info">
								<span class="setting-name">{plugin.manifest.name}</span>
								<span class="setting-desc"
									>{plugin.manifest.description || `v${plugin.manifest.version}`}</span
								>
							</div>
							<div class="toggle" class:active={plugin.enabled}>
								<div class="toggle-knob"></div>
							</div>
						</button>
					{/each}
				</div>
			</section>
		{/if}

		{#each settingsTabs as tab (tab.id)}
			{@const Component = tab.component}
			<section>
				<h2>{tab.title}</h2>
				<div class="plugin-settings">
					<Component />
				</div>
			</section>
		{/each}
	</main>
</div>

<style>
	.settings {
		height: 100vh;
		overflow-y: auto;
		background-color: var(--color-base);
	}

	header {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 16px;
		background-color: var(--color-surface);
		border-bottom: 1px solid var(--color-overlay);
	}

	header h1 {
		font-size: 20px;
		font-weight: 600;
	}

	.back-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		color: var(--color-text);
		border-radius: 8px;
		cursor: pointer;
	}

	.back-btn:hover {
		background-color: var(--color-overlay);
	}

	main {
		padding: 24px;
		max-width: 600px;
	}

	section + section {
		margin-top: 24px;
	}

	section h2 {
		font-size: 16px;
		color: var(--color-accent);
		margin-bottom: 16px;
	}

	.theme-grid {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.theme-card {
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 16px;
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 12px;
		cursor: pointer;
		text-align: left;
	}

	.theme-card:hover {
		background-color: var(--color-overlay);
	}

	.theme-card.selected {
		border-color: var(--color-accent);
		border-width: 2px;
	}

	.preview-colors {
		display: flex;
		gap: 4px;
	}

	.color {
		width: 24px;
		height: 24px;
		border-radius: 4px;
		border: 1px solid var(--color-overlay);
	}

	.theme-info {
		flex: 1;
		display: flex;
		flex-direction: column;
	}

	.theme-name {
		font-weight: 500;
		color: var(--color-text);
	}

	.theme-type {
		font-size: 12px;
		color: var(--color-subtext);
	}

	.check {
		flex-shrink: 0;
	}

	.setting-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 16px;
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 12px;
		cursor: pointer;
		text-align: left;
	}

	.setting-row:hover {
		background-color: var(--color-overlay);
	}

	.setting-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.setting-name {
		font-weight: 500;
		color: var(--color-text);
	}

	.setting-desc {
		font-size: 12px;
		color: var(--color-subtext);
	}

	.toggle {
		width: 44px;
		height: 24px;
		background-color: var(--color-overlay);
		border-radius: 12px;
		padding: 2px;
		transition: background-color 0.2s;
	}

	.toggle.active {
		background-color: var(--color-accent);
	}

	.toggle-knob {
		width: 20px;
		height: 20px;
		background-color: var(--color-text);
		border-radius: 50%;
		transition: transform 0.2s;
	}

	.toggle.active .toggle-knob {
		transform: translateX(20px);
	}

	.plugin-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.plugin-settings {
		background: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 12px;
		padding: 16px;
	}
</style>
