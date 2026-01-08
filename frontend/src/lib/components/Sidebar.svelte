<script lang="ts">
	import { filesystemActions } from '$lib/stores/filesystem';
	import FileTree from './FileTree.svelte';

	interface Props {
		onCreateFile: () => void;
		onCreateFolder: () => void;
	}

	let { onCreateFile, onCreateFolder }: Props = $props();

	let searchQuery = $state('');
	let isSearching = $state(false);

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
		<div class="actions">
			<button class="action-btn" onclick={onCreateFile} title="New file">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
					<path
						d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 14h-3v3h-2v-3H8v-2h3v-3h2v3h3v2zm-3-7V3.5L18.5 9H13z"
					/>
				</svg>
			</button>
			<button class="action-btn" onclick={onCreateFolder} title="New folder">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
					<path
						d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-1 8h-3v3h-2v-3h-3v-2h3V9h2v3h3v2z"
					/>
				</svg>
			</button>
		</div>
	</div>
	<FileTree />
</aside>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		width: 280px;
		min-width: 200px;
		max-width: 400px;
		background-color: var(--color-mantle);
		border-right: 1px solid var(--color-overlay);
	}

	.header {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 12px;
		border-bottom: 1px solid var(--color-overlay);
	}

	.search-container {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 12px;
		background-color: var(--color-surface);
		border-radius: 8px;
	}

	.search-container input {
		flex: 1;
		border: none;
		background: transparent;
		color: var(--color-text);
		font-size: 14px;
		outline: none;
	}

	.search-container input::placeholder {
		color: var(--color-subtext);
	}

	.actions {
		display: flex;
		gap: 4px;
	}

	.action-btn {
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

	.action-btn:hover {
		background-color: var(--color-overlay);
	}
</style>
