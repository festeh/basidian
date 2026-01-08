<script lang="ts">
	import { rootNodes, isLoading, filesystemActions, selectedNode } from '$lib/stores/filesystem';
	import FileTreeItem from './FileTreeItem.svelte';
	import ContextMenu from './ContextMenu.svelte';

	interface Props {
		onCreateFile: () => void;
		onCreateFolder: () => void;
	}

	let { onCreateFile, onCreateFolder }: Props = $props();

	let contextMenu = $state<{ x: number; y: number } | null>(null);
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

	async function handleDelete() {
		const node = $selectedNode;
		if (!node) return;

		const confirmed = confirm(`Delete "${node.name}"?`);
		if (confirmed) {
			await filesystemActions.deleteNode(node);
		}
	}

	const menuItems = $derived([
		{ label: 'New File', action: () => onCreateFile() },
		{ label: 'New Folder', action: () => onCreateFolder() },
		...($selectedNode
			? [{ label: 'Delete', action: () => handleDelete(), danger: true }]
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
