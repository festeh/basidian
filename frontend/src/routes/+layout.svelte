<script lang="ts">
	import { onMount } from 'svelte';
	import { currentTheme, applyTheme } from '$lib/stores/theme';
	import { settings } from '$lib/stores/settings';
	import { applySafeAreaInsets } from '$lib/utils/safe-area';
	import { migratePluginStorageKeys } from '$lib/utils/migrate-storage';
	import '../app.css';

	let { children } = $props();

	onMount(() => {
		applyTheme($currentTheme);
		applySafeAreaInsets();
		migratePluginStorageKeys();
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
