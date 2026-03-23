<script lang="ts">
	import { syncState, syncSummary, syncError, pendingCount } from '$lib/sync/status';
	import { syncNow } from '$lib/sync/engine';

	let showError = $state(false);

	function handleClick() {
		if ($syncState === 'error') {
			showError = !showError;
		} else {
			syncNow();
		}
	}
</script>

<button
	class="sync-indicator"
	class:synced={$syncState === 'synced'}
	class:pending={$syncState === 'pending'}
	class:syncing={$syncState === 'syncing'}
	class:error={$syncState === 'error'}
	class:uninitialized={$syncState === 'uninitialized'}
	onclick={handleClick}
	title={$syncState === 'error' ? 'Click for details' : 'Click to sync now'}
>
	{#if $syncState === 'syncing'}
		<svg class="icon spinning" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<path d="M21 12a9 9 0 1 1-6.219-8.56" />
		</svg>
	{:else if $syncState === 'synced'}
		<svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<polyline points="20 6 9 17 4 12" />
		</svg>
	{:else if $syncState === 'error'}
		<svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<circle cx="12" cy="12" r="10" />
			<line x1="12" y1="8" x2="12" y2="12" />
			<line x1="12" y1="16" x2="12.01" y2="16" />
		</svg>
	{:else if $syncState === 'pending'}
		<svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<polyline points="17 1 21 5 17 9" />
			<path d="M3 11V9a4 4 0 0 1 4-4h14" />
			<polyline points="7 23 3 19 7 15" />
			<path d="M21 13v2a4 4 0 0 1-4 4H3" />
		</svg>
	{:else}
		<svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<circle cx="12" cy="12" r="10" />
			<line x1="8" y1="12" x2="16" y2="12" />
		</svg>
	{/if}
	<span class="label">{$syncSummary}</span>
</button>

{#if showError && $syncError}
	<div class="error-detail">
		<p>{$syncError}</p>
		<button class="retry-btn" onclick={() => { showError = false; syncNow(); }}>
			Retry
		</button>
	</div>
{/if}

<style>
	.sync-indicator {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 10px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		font-size: var(--text-detail);
		font-family: inherit;
		cursor: pointer;
		border-radius: var(--radius-default);
		white-space: nowrap;
	}

	.sync-indicator:hover {
		background: var(--color-overlay);
		color: var(--color-text);
	}

	.sync-indicator.synced {
		color: var(--color-success);
	}

	.sync-indicator.pending {
		color: var(--color-secondary);
	}

	.sync-indicator.syncing {
		color: var(--color-accent);
	}

	.sync-indicator.error {
		color: var(--color-error);
	}

	.sync-indicator.uninitialized {
		color: var(--color-subtext);
	}

	.icon {
		flex-shrink: 0;
	}

	.spinning {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.label {
		line-height: 1;
	}

	.error-detail {
		position: fixed;
		bottom: calc(36px + var(--safe-area-inset-bottom));
		left: calc(8px + var(--safe-area-inset-left));
		background: var(--color-surface);
		border: 1px solid var(--color-error);
		border-radius: var(--radius-default);
		padding: var(--space-compact) var(--space-cozy);
		color: var(--color-text);
		font-size: var(--text-detail);
		box-shadow: var(--shadow-subtle);
		max-width: 360px;
		z-index: var(--z-modal);
	}

	.error-detail p {
		margin: 0 0 var(--space-compact);
		word-break: break-word;
	}

	.retry-btn {
		padding: 4px 12px;
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-default);
		background: var(--color-mantle);
		color: var(--color-text);
		font-size: var(--text-detail);
		font-family: inherit;
		cursor: pointer;
	}

	.retry-btn:hover {
		background: var(--color-overlay);
	}
</style>
