<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { currentTheme, applyTheme } from '$lib/stores/theme';
	import { settings } from '$lib/stores/settings';
	import { applySafeAreaInsets } from '$lib/utils/safe-area';
	import { migratePluginStorageKeys } from '$lib/utils/migrate-storage';
	import { start as startSync, stop as stopSync } from '$lib/sync/engine';
	import '../app.css';

	let { children } = $props();

	onMount(() => {
		applyTheme($currentTheme);
		applySafeAreaInsets();
		migratePluginStorageKeys();
		startSync();
	});

	onDestroy(() => {
		stopSync();
	});

	$effect(() => {
		applyTheme($currentTheme);

		const root = document.documentElement;
		if ($settings.accentColor) {
			root.style.setProperty('--color-accent', $settings.accentColor);
		}
	});

	// Apply font size reactively
	$effect(() => {
		document.documentElement.style.setProperty('--font-size-base', `${$settings.fontSize}px`);
	});
</script>

{@render children()}
