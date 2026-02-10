<script lang="ts">
	import { uiRegistry } from './ui-registry';
	import type { UISlotItem } from './ui-registry';

	interface Props {
		slot: 'statusBar' | 'editorToolbar';
	}

	let { slot }: Props = $props();

	// Subscribe to the appropriate store based on slot type
	let statusBarItems: UISlotItem[] = $state([]);
	let editorToolbarItems: UISlotItem[] = $state([]);

	uiRegistry.statusBarItems.subscribe((value) => (statusBarItems = value));
	uiRegistry.editorToolbarItems.subscribe((value) => (editorToolbarItems = value));

	const items = $derived(slot === 'statusBar' ? statusBarItems : editorToolbarItems);
</script>

{#if items.length > 0}
	<div class="plugin-slot plugin-slot-{slot}">
		{#each items as item (item.id)}
			{@const Component = item.component}
			<Component {...item.props} />
		{/each}
	</div>
{/if}

<style>
	.plugin-slot {
		display: flex;
		align-items: center;
		gap: var(--space-compact);
	}
</style>
