<script lang="ts">
	import { rootNodes, isLoading } from '$lib/stores/filesystem';
	import FileTreeItem from './FileTreeItem.svelte';
</script>

<div class="file-tree">
	{#if $isLoading}
		<div class="loading">
			<div class="spinner"></div>
		</div>
	{:else if $rootNodes.length === 0}
		<div class="empty">
			<p>No files yet</p>
			<p class="hint">Create a new file to get started</p>
		</div>
	{:else}
		{#each $rootNodes as node (node.id || node.path)}
			<FileTreeItem {node} />
		{/each}
	{/if}
</div>

<style>
	.file-tree {
		flex: 1;
		overflow-y: auto;
		padding: 8px;
	}

	.loading {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 32px;
	}

	.spinner {
		width: 24px;
		height: 24px;
		border: 2px solid var(--color-overlay);
		border-top-color: var(--color-accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 32px;
		color: var(--color-subtext);
		text-align: center;
	}

	.empty p {
		margin: 0;
	}

	.empty .hint {
		font-size: 12px;
		margin-top: 4px;
	}
</style>
