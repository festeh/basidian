<script lang="ts">
	import { tick } from 'svelte';
	import type { FsNode } from '$lib/types';
	import { selectedNode, filesystemActions, renamingPath, movingNode } from '$lib/stores/filesystem';
	import FileTreeItem from './FileTreeItem.svelte';

	interface Props {
		node: FsNode;
		depth?: number;
	}

	let { node, depth = 0 }: Props = $props();

	const isSelected = $derived($selectedNode?.id === node.id);
	const hasChildren = $derived(node.children && node.children.length > 0);
	const isFolder = $derived(node.type === 'folder');
	const isRenaming = $derived($renamingPath === node.path);
	const isMoving = $derived($movingNode?.id === node.id);

	let renameInput = $state<HTMLInputElement>();
	let renameValue = $state('');

	$effect(() => {
		if (isRenaming) {
			renameValue = node.name;
			tick().then(() => {
				if (renameInput) {
					renameInput.focus();
					// Select name without extension for files
					const dotIndex = node.type === 'file' ? renameValue.lastIndexOf('.') : -1;
					renameInput.setSelectionRange(0, dotIndex > 0 ? dotIndex : renameValue.length);
				}
			});
		}
	});

	async function commitRename() {
		renamingPath.set(null);
		const trimmed = renameValue.trim();
		if (trimmed && trimmed !== node.name) {
			await filesystemActions.renameNode(node, trimmed);
		}
	}

	function cancelRename() {
		renamingPath.set(null);
	}

	function handleRenameKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			commitRename();
		} else if (e.key === 'Escape') {
			e.preventDefault();
			cancelRename();
		}
	}

	function handleClick() {
		filesystemActions.selectNode(node);
		if (node.type === 'file') {
			filesystemActions.openFile(node);
		} else {
			filesystemActions.toggleFolder(node);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			handleClick();
		}
	}

	function handleContextMenu() {
		// Select node on right-click so context menu shows correct options
		filesystemActions.selectNode(node);
	}

	// Drag source (the node being moved)
	function handleDragStart(e: DragEvent) {
		if (!isMoving || !e.dataTransfer) return;
		e.dataTransfer.effectAllowed = 'move';
		e.dataTransfer.setData('text/plain', node.id!);
	}

	function handleDragEnd() {
		movingNode.set(null);
	}

	// Drop target (folders only)
	let isDropTarget = $state(false);

	function isDescendantOfMoving(folderPath: string): boolean {
		const moving = $movingNode;
		if (!moving) return false;
		// Can't drop onto self
		if (moving.id === node.id) return true;
		// Can't drop onto own descendant
		if (moving.type === 'folder' && folderPath.startsWith(moving.path + '/')) return true;
		return false;
	}

	function handleDragOver(e: DragEvent) {
		if (!$movingNode || !isFolder) return;
		if (isDescendantOfMoving(node.path)) return;
		// Don't highlight if already the parent
		if ($movingNode.parent_path === node.path) return;
		e.preventDefault();
		isDropTarget = true;
	}

	function handleDragLeave() {
		isDropTarget = false;
	}

	function handleDrop(e: DragEvent) {
		isDropTarget = false;
		if (!$movingNode || !isFolder) return;
		if (isDescendantOfMoving(node.path)) return;
		if ($movingNode.parent_path === node.path) return;
		e.preventDefault();
		e.stopPropagation();
		filesystemActions.moveNode($movingNode, node.path);
	}
</script>

<div class="tree-item">
	<button
		class="item-row"
		class:selected={isSelected}
		class:moving={isMoving}
		class:drop-target={isDropTarget}
		style="padding-left: {depth * 16 + 8}px"
		draggable={isMoving}
		onclick={handleClick}
		onkeydown={handleKeydown}
		oncontextmenu={handleContextMenu}
		ondragstart={handleDragStart}
		ondragend={handleDragEnd}
		ondragover={handleDragOver}
		ondragleave={handleDragLeave}
		ondrop={handleDrop}
	>
		{#if isFolder}
			<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--color-secondary)">
				<path
					d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
				/>
			</svg>
		{:else}
			<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--color-accent)">
				<path
					d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"
				/>
			</svg>
		{/if}
		{#if isRenaming}
			<!-- svelte-ignore a11y_autofocus -->
			<input
				class="rename-input"
				bind:this={renameInput}
				bind:value={renameValue}
				onkeydown={handleRenameKeydown}
				onblur={commitRename}
				onclick={(e) => e.stopPropagation()}
			/>
		{:else}
			<span class="name">{node.name}</span>
		{/if}
		{#if isFolder}
			<span class="toggle-icon" class:rotated={node.isExpanded}>
				<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
					<path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
				</svg>
			</span>
		{/if}
	</button>

	{#if isFolder && node.isExpanded && hasChildren}
		<div class="children">
			{#each node.children as child (child.id || child.path)}
				<FileTreeItem node={child} depth={depth + 1} />
			{/each}
		</div>
	{/if}
</div>

<style>
	.tree-item {
		width: 100%;
	}

	.item-row {
		display: flex;
		align-items: center;
		gap: var(--space-snug);
		width: 100%;
		padding: var(--space-snug) var(--space-compact);
		border: none;
		background: transparent;
		color: var(--color-text);
		text-align: left;
		cursor: pointer;
		border-radius: var(--radius-default);
		font-size: var(--text-body);
	}

	.item-row:hover {
		background-color: var(--color-overlay);
	}

	.item-row.selected {
		background-color: color-mix(in srgb, var(--color-accent) 15%, transparent);
		border-left: 3px solid var(--color-accent);
	}

	.item-row.moving {
		opacity: 0.6;
		outline: 2px dashed var(--color-accent);
		outline-offset: -2px;
		cursor: grab;
	}

	.item-row.drop-target {
		background-color: color-mix(in srgb, var(--color-accent) 20%, transparent);
		outline: 2px solid var(--color-accent);
		outline-offset: -2px;
	}

	.toggle-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		color: var(--color-subtext);
		transition: transform 0.15s ease;
		transform: rotate(-90deg);
	}

	.toggle-icon.rotated {
		transform: rotate(0deg);
	}

	.name {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.rename-input {
		flex: 1;
		min-width: 0;
		padding: 0 var(--space-tight);
		border: 1px solid var(--color-accent);
		border-radius: var(--radius-subtle);
		background: var(--color-base);
		color: var(--color-text);
		font-size: var(--text-body);
		font-family: inherit;
		outline: none;
	}

	.children {
		width: 100%;
	}
</style>
