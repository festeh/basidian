<script lang="ts">
	import { onMount } from 'svelte';
	import { currentTheme, applyTheme } from '$lib/stores/theme';
	import { settings } from '$lib/stores/settings';
	import { pluginManager } from '$lib/plugins';
	import { applySafeAreaInsets } from '$lib/utils/safe-area';
	import '../app.css';

	let { children } = $props();

	// Apply theme on mount and whenever it changes
	onMount(() => {
		applyTheme($currentTheme);
		// Initialize plugin system
		pluginManager.initialize();
		// Apply native safe area insets on mobile
		applySafeAreaInsets();
	});

	$effect(() => {
		applyTheme($currentTheme);
		// Notify plugins of theme changes
		pluginManager.dispatchThemeChange($currentTheme);

		// Apply accent color override after theme
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
