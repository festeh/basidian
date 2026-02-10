<script lang="ts">
	import { filesystemActions } from '$lib/stores/filesystem';
	import { uiRegistry, type UISlotItem } from '$lib/plugins';
	import FileTree from './FileTree.svelte';

	interface Props {
		onCreateFile: () => void;
		onCreateFolder: () => void;
	}

	let { onCreateFile, onCreateFolder }: Props = $props();

	let searchQuery = $state('');
	let isSearching = $state(false);
	let sidebarActions: UISlotItem[] = $state([]);

	uiRegistry.sidebarActions.subscribe((items) => (sidebarActions = items));

	async function handleSearch() {
		if (!searchQuery.trim()) return;
		isSearching = true;
		await filesystemActions.searchFiles(searchQuery);
		isSearching = false;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			handleSearch();
		}
	}
</script>

<aside class="sidebar">
	<div class="header">
		<div class="search-container">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="var(--color-subtext)">
				<path
					d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
				/>
			</svg>
			<input
				type="text"
				placeholder="Search..."
				bind:value={searchQuery}
				onkeydown={handleKeydown}
			/>
		</div>
		{#if sidebarActions.length > 0}
			<div class="sidebar-actions">
				{#each sidebarActions as item (item.id)}
					{@const Component = item.component}
					<Component {...item.props} />
				{/each}
			</div>
		{/if}
	</div>
	<FileTree {onCreateFile} {onCreateFolder} />
</aside>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		width: 280px;
		min-width: 200px;
		max-width: 400px;
		background-color: var(--color-mantle);
		z-index: var(--z-raised);
	}

	.header {
		display: flex;
		flex-direction: column;
		gap: var(--space-compact);
		padding: var(--space-cozy);
		border-bottom: 1px solid var(--color-overlay);
	}

	.search-container {
		display: flex;
		align-items: center;
		gap: var(--space-compact);
		padding: var(--space-compact) var(--space-cozy);
		background-color: var(--color-surface);
		border-radius: var(--radius-rounded);
	}

	.search-container input {
		flex: 1;
		border: none;
		background: transparent;
		color: var(--color-text);
		font-size: var(--text-body);
		outline: none;
	}

	.search-container input::placeholder {
		color: var(--color-subtext);
	}

	.sidebar-actions {
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: var(--space-tight);
	}
</style>
