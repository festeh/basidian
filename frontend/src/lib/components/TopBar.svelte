<script lang="ts">
	import { getCurrentWindow } from '@tauri-apps/api/window';

	interface Props {
		sidebarCollapsed: boolean;
		onToggleSidebar: () => void;
		onOpenSettings: () => void;
		onOpenInfo: () => void;
	}

	let { sidebarCollapsed, onToggleSidebar, onOpenSettings, onOpenInfo }: Props = $props();

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
	<div class="left">
		<button
			class="icon-btn"
			onmousedown={(e) => e.stopPropagation()}
			onclick={onToggleSidebar}
			title={sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
		>
			{#if sidebarCollapsed}
				<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
					<path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
				</svg>
			{:else}
				<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
					<path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
				</svg>
			{/if}
		</button>
	</div>

	<div class="right">
		<button
			class="icon-btn"
			onmousedown={(e) => e.stopPropagation()}
			onclick={onOpenInfo}
			title="Info"
		>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
			</svg>
		</button>
		<button
			class="icon-btn"
			onmousedown={(e) => e.stopPropagation()}
			onclick={onOpenSettings}
			title="Settings"
		>
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path
					d="M19.14,12.94c0.04-0.31,0.06-0.63,0.06-0.94c0-0.31-0.02-0.63-0.06-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.37,4.82,11.69,4.82,12s0.02,0.63,0.06,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"
				/>
			</svg>
		</button>

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
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		color: var(--color-text);
		border-radius: 8px;
		cursor: pointer;
	}

	.icon-btn:hover {
		background-color: var(--color-overlay);
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
