<script lang="ts">
	import { onMount } from 'svelte';
	import { currentTheme, applyTheme } from '$lib/stores/theme';
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
	});
</script>

{@render children()}
