<script lang="ts">
	import type { FsNode } from '$lib/types';
	import { selectedNode, filesystemActions } from '$lib/stores/filesystem';
	import FileTreeItem from './FileTreeItem.svelte';

	interface Props {
		node: FsNode;
		depth?: number;
	}

	let { node, depth = 0 }: Props = $props();

	const isSelected = $derived($selectedNode?.id === node.id);
	const hasChildren = $derived(node.children && node.children.length > 0);
	const isFolder = $derived(node.type === 'folder');

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
</script>

<div class="tree-item">
	<button
		class="item-row"
		class:selected={isSelected}
		style="padding-left: {depth * 16 + 8}px"
		onclick={handleClick}
		onkeydown={handleKeydown}
	>
		{#if isFolder}
			<span class="toggle-icon" class:rotated={node.isExpanded}>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
					<path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
				</svg>
			</span>
			<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--color-secondary)">
				<path
					d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"
				/>
			</svg>
		{:else}
			<span class="spacer"></span>
			<svg width="18" height="18" viewBox="0 0 24 24" fill="var(--color-accent)">
				<path
					d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"
				/>
			</svg>
		{/if}
		<span class="name">{node.name}</span>
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
		gap: 6px;
		width: 100%;
		padding: 6px 8px;
		border: none;
		background: transparent;
		color: var(--color-text);
		text-align: left;
		cursor: pointer;
		border-radius: 6px;
		font-size: 14px;
	}

	.item-row:hover {
		background-color: var(--color-overlay);
	}

	.item-row.selected {
		background-color: var(--color-accent);
		color: var(--color-base);
	}

	.item-row.selected :global(svg) {
		fill: var(--color-base);
	}

	.toggle-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		color: var(--color-subtext);
		transition: transform 0.15s ease;
	}

	.toggle-icon.rotated {
		transform: rotate(90deg);
	}

	.spacer {
		width: 20px;
	}

	.name {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.children {
		width: 100%;
	}
</style>
