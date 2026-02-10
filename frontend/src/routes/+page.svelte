<script lang="ts">
	import { isMobile } from '$lib/stores/platform';
	import PageDesktop from './PageDesktop.svelte';
	import PageMobile from './PageMobile.svelte';
</script>

{#if isMobile}
	<PageMobile />
{:else}
	<PageDesktop />
{/if}

<style>
	/* Modal form styles (shared globally) */
	:global(.input) {
		width: 100%;
		padding: var(--space-cozy);
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-rounded);
		background-color: var(--color-base);
		color: var(--color-text);
		font-size: var(--text-body);
		outline: none;
	}

	:global(.input:focus) {
		border-color: var(--color-accent);
	}

	:global(.btn) {
		padding: 10px 20px;
		border: none;
		border-radius: var(--radius-rounded);
		font-size: var(--text-body);
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.15s;
	}

	:global(.btn:disabled) {
		opacity: 0.5;
		cursor: not-allowed;
	}

	:global(.btn.primary) {
		background-color: var(--color-accent);
		color: var(--color-base);
	}

	:global(.btn.primary:hover:not(:disabled)) {
		filter: brightness(1.1);
	}

	:global(.btn.secondary) {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	:global(.btn.secondary:hover:not(:disabled)) {
		background-color: var(--color-subtext);
	}
</style>
