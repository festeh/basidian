<script lang="ts">
	import { onMount } from 'svelte';

	interface MenuItem {
		label: string;
		icon?: string;
		action: () => void;
		danger?: boolean;
	}

	interface Props {
		x: number;
		y: number;
		items: MenuItem[];
		onclose: () => void;
	}

	let { x, y, items, onclose }: Props = $props();
	let menuRef: HTMLDivElement;

	onMount(() => {
		// Adjust position if menu would overflow viewport
		const rect = menuRef.getBoundingClientRect();
		if (rect.right > window.innerWidth) {
			menuRef.style.left = `${window.innerWidth - rect.width - 8}px`;
		}
		if (rect.bottom > window.innerHeight) {
			menuRef.style.top = `${window.innerHeight - rect.height - 8}px`;
		}

		// Close on click outside
		function handleClickOutside(e: MouseEvent) {
			if (menuRef && !menuRef.contains(e.target as Node)) {
				onclose();
			}
		}

		// Close on escape
		function handleKeydown(e: KeyboardEvent) {
			if (e.key === 'Escape') {
				onclose();
			}
		}

		document.addEventListener('mousedown', handleClickOutside);
		document.addEventListener('keydown', handleKeydown);

		return () => {
			document.removeEventListener('mousedown', handleClickOutside);
			document.removeEventListener('keydown', handleKeydown);
		};
	});

	function handleItemClick(item: MenuItem) {
		item.action();
		onclose();
	}
</script>

<div class="context-menu" bind:this={menuRef} style="left: {x}px; top: {y}px">
	{#each items as item}
		<button
			class="menu-item"
			class:danger={item.danger}
			onclick={() => handleItemClick(item)}
		>
			{item.label}
		</button>
	{/each}
</div>

<style>
	.context-menu {
		position: fixed;
		z-index: var(--z-modal);
		min-width: 160px;
		padding: var(--space-tight);
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-rounded);
		box-shadow: var(--shadow-raised);
	}

	.menu-item {
		display: flex;
		align-items: center;
		width: 100%;
		padding: var(--space-compact) var(--space-cozy);
		border: none;
		background: transparent;
		color: var(--color-text);
		font-size: var(--text-body);
		text-align: left;
		cursor: pointer;
		border-radius: var(--radius-subtle);
	}

	.menu-item:hover {
		background-color: var(--color-overlay);
	}

	.menu-item.danger {
		color: var(--color-error);
	}

	.menu-item.danger:hover {
		background-color: var(--color-error);
		color: var(--color-base);
	}
</style>
