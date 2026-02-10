<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		open: boolean;
		title: string;
		onClose: () => void;
		children: Snippet;
		actions?: Snippet;
	}

	let { open, title, onClose, children, actions }: Props = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleBackdropKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' || e.key === ' ') {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="backdrop"
		onclick={handleBackdropClick}
		onkeydown={handleBackdropKeydown}
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
		tabindex="-1"
	>
		<div class="modal">
			<div class="header">
				<h2 id="modal-title">{title}</h2>
				<button class="close-btn" onclick={onClose} aria-label="Close">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
						<path
							d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
						/>
					</svg>
				</button>
			</div>
			<div class="content">
				{@render children()}
			</div>
			{#if actions}
				<div class="actions">
					{@render actions()}
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: var(--color-backdrop);
		z-index: var(--z-modal);
	}

	.modal {
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: 400px;
		background-color: var(--color-surface);
		border-radius: var(--radius-prominent);
		box-shadow: var(--shadow-floating);
	}

	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-comfortable);
		border-bottom: 1px solid var(--color-overlay);
	}

	.header h2 {
		margin: 0;
		font-size: var(--text-heading);
		font-weight: 600;
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		border-radius: var(--radius-rounded);
		cursor: pointer;
	}

	.close-btn:hover {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.content {
		padding: var(--space-comfortable);
	}

	.actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-compact);
		padding: var(--space-comfortable);
		border-top: 1px solid var(--color-overlay);
	}
</style>
