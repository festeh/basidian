<script lang="ts">
	import { getCurrentWindow } from '@tauri-apps/api/window';
	import TopBar from './TopBar.svelte';

	interface Props {
		onOpenSettings: () => void;
		onOpenInfo: () => void;
	}

	let { onOpenSettings, onOpenInfo }: Props = $props();

	const appWindow = getCurrentWindow();

	async function startDragging(e: MouseEvent) {
		if (e.buttons === 1) {
			await appWindow.startDragging();
		}
	}

	async function minimizeWindow() {
		await appWindow.minimize();
	}

	async function toggleMaximize() {
		await appWindow.toggleMaximize();
	}

	async function closeWindow() {
		await appWindow.close();
	}
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div class="topbar" onmousedown={startDragging} role="banner">
	<div class="drag-spacer"></div>

	<div class="right">
		<TopBar {onOpenSettings} {onOpenInfo} />

		<div class="window-controls">
			<button
				class="window-btn"
				onmousedown={(e) => e.stopPropagation()}
				onclick={minimizeWindow}
				title="Minimize"
			>
				<svg width="12" height="12" viewBox="0 0 12 12">
					<rect x="2" y="5.5" width="8" height="1" fill="currentColor" />
				</svg>
			</button>
			<button
				class="window-btn"
				onmousedown={(e) => e.stopPropagation()}
				onclick={toggleMaximize}
				title="Maximize"
			>
				<svg width="12" height="12" viewBox="0 0 12 12">
					<rect x="2" y="2" width="8" height="8" stroke="currentColor" fill="none" stroke-width="1"
					/>
				</svg>
			</button>
			<button
				class="window-btn close"
				onmousedown={(e) => e.stopPropagation()}
				onclick={closeWindow}
				title="Close"
			>
				<svg width="12" height="12" viewBox="0 0 12 12">
					<path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" />
				</svg>
			</button>
		</div>
	</div>
</div>

<style>
	.topbar {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 4px 4px 0;
		background-color: var(--color-base);
		z-index: 2;
		user-select: none;
		-webkit-user-select: none;
	}

	.drag-spacer {
		flex: 1;
	}

	.right {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.window-controls {
		display: flex;
		margin-left: 12px;
	}

	.window-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		cursor: pointer;
	}

	.window-btn:hover {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.window-btn.close:hover {
		background-color: var(--color-error);
		color: white;
	}
</style>
