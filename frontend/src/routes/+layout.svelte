<script lang="ts">
	import { onMount } from 'svelte';
	import { currentTheme, applyTheme } from '$lib/stores/theme';
	import '../app.css';

	let { children } = $props();

	// Apply theme on mount and whenever it changes
	onMount(() => {
		applyTheme($currentTheme);
	});

	$effect(() => {
		applyTheme($currentTheme);
	});
</script>

{@render children()}
