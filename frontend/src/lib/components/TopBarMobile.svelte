<script lang="ts">
	import TopBar from './TopBar.svelte';

	interface Props {
		onToggleSidebar: () => void;
		onOpenSettings: () => void;
		onOpenInfo: () => void;
	}

	let { onToggleSidebar, onOpenSettings, onOpenInfo }: Props = $props();
</script>

<div class="topbar" role="banner">
	<div class="left">
		<button
			class="icon-btn"
			onclick={onToggleSidebar}
			title="Menu"
		>
			<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
				<path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
			</svg>
		</button>
	</div>

	<div class="right">
		<TopBar {onOpenSettings} {onOpenInfo} />
	</div>
</div>

<style>
	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 8px 12px;
		background-color: var(--color-surface);
		user-select: none;
		-webkit-user-select: none;
	}

	.left,
	.right {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 44px;
		height: 44px;
		border: none;
		background: transparent;
		color: var(--color-text);
		border-radius: 8px;
		cursor: pointer;
	}

	.icon-btn:hover {
		background-color: var(--color-overlay);
	}
</style>
