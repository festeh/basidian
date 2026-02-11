<script lang="ts">
	import type { FsNode } from '$lib/types';
	import { rootNodes, isLoading, error, filesystemActions, selectedNode } from '$lib/stores/filesystem';
	import FileTreeItem from './FileTreeItem.svelte';
	import ContextMenu from './ContextMenu.svelte';
	import ConfirmDialog from './ConfirmDialog.svelte';

	interface Props {
		onCreateFile: () => void;
		onCreateFolder: () => void;
	}

	let { onCreateFile, onCreateFolder }: Props = $props();

	let contextMenu = $state<{ x: number; y: number } | null>(null);
	let deleteTarget = $state<FsNode | null>(null);
	let longPressTimer: ReturnType<typeof setTimeout> | null = null;

	function handleContextMenu(e: MouseEvent) {
		e.preventDefault();
		contextMenu = { x: e.clientX, y: e.clientY };
	}

	function handleTouchStart(e: TouchEvent) {
		const touch = e.touches[0];
		longPressTimer = setTimeout(() => {
			contextMenu = { x: touch.clientX, y: touch.clientY };
		}, 500);
	}

	function handleTouchEnd() {
		if (longPressTimer) {
			clearTimeout(longPressTimer);
			longPressTimer = null;
		}
	}

	function closeContextMenu() {
		contextMenu = null;
	}

	function handleDeleteClick() {
		deleteTarget = $selectedNode;
	}

	async function confirmDelete() {
		if (deleteTarget) {
			await filesystemActions.deleteNode(deleteTarget);
		}
		deleteTarget = null;
	}

	function cancelDelete() {
		deleteTarget = null;
	}

	const menuItems = $derived([
		{ label: 'New File', action: () => onCreateFile() },
		{ label: 'New Folder', action: () => onCreateFolder() },
		...($selectedNode
			? [{ label: 'Delete', action: handleDeleteClick, danger: true }]
			: [])
	]);
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class="file-tree"
	oncontextmenu={handleContextMenu}
	ontouchstart={handleTouchStart}
	ontouchend={handleTouchEnd}
	ontouchmove={handleTouchEnd}
>
	{#if $isLoading}
		<div class="loading">
			<div class="spinner"></div>
		</div>
	{:else if $error}
		<div class="error-state">
			<p>Could not connect to server</p>
			<p class="hint">{$error}</p>
			<button class="retry-btn" onclick={() => filesystemActions.loadTree()}>Retry</button>
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

{#if contextMenu}
	<ContextMenu
		x={contextMenu.x}
		y={contextMenu.y}
		items={menuItems}
		onclose={closeContextMenu}
	/>
{/if}

{#if deleteTarget}
	<ConfirmDialog
		title="Delete {deleteTarget.type === 'folder' ? 'Folder' : 'File'}"
		message="Are you sure you want to delete &quot;{deleteTarget.name}&quot;? This action cannot be undone."
		confirmLabel="Delete"
		danger={true}
		onconfirm={confirmDelete}
		oncancel={cancelDelete}
	/>
{/if}

<style>
	.file-tree {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-compact);
	}

	.loading {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-wide);
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

	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-wide);
		color: var(--color-subtext);
		text-align: center;
	}

	.error-state p {
		margin: 0;
	}

	.error-state .hint {
		font-size: var(--text-label);
		margin-top: var(--space-tight);
		color: var(--color-error);
	}

	.retry-btn {
		margin-top: var(--space-base);
		padding: var(--space-tight) var(--space-base);
		background: var(--color-overlay);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		cursor: pointer;
		font-size: var(--text-body);
	}

	.retry-btn:hover {
		background: var(--color-surface);
	}

	.empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-wide);
		color: var(--color-subtext);
		text-align: center;
	}

	.empty p {
		margin: 0;
	}

	.empty .hint {
		font-size: var(--text-label);
		margin-top: var(--space-tight);
	}
</style>
