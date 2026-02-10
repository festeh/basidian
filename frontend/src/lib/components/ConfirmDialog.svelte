<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		title: string;
		message: string;
		confirmLabel?: string;
		cancelLabel?: string;
		danger?: boolean;
		onconfirm: () => void;
		oncancel: () => void;
	}

	let {
		title,
		message,
		confirmLabel = 'Delete',
		cancelLabel = 'Cancel',
		danger = false,
		onconfirm,
		oncancel
	}: Props = $props();

	let dialogRef: HTMLDivElement;

	onMount(() => {
		// Focus the cancel button by default for safety
		dialogRef.querySelector('button')?.focus();

		function handleKeydown(e: KeyboardEvent) {
			if (e.key === 'Escape') {
				oncancel();
			}
		}

		document.addEventListener('keydown', handleKeydown);
		return () => document.removeEventListener('keydown', handleKeydown);
	});
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div class="overlay" onclick={oncancel} role="presentation">
	<!-- svelte-ignore a11y_interactive_supports_focus -->
	<div
		class="dialog"
		bind:this={dialogRef}
		onclick={(e) => e.stopPropagation()}
		role="dialog"
		aria-modal="true"
		aria-labelledby="dialog-title"
		aria-describedby="dialog-message"
	>
		<h2 id="dialog-title">{title}</h2>
		<p id="dialog-message">{message}</p>
		<div class="actions">
			<button class="btn cancel" onclick={oncancel}>
				{cancelLabel}
			</button>
			<button class="btn confirm" class:danger onclick={onconfirm}>
				{confirmLabel}
			</button>
		</div>
	</div>
</div>

<style>
	.overlay {
		position: fixed;
		inset: 0;
		z-index: var(--z-modal);
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: var(--color-backdrop);
	}

	.dialog {
		min-width: 300px;
		max-width: 400px;
		padding: var(--space-loose);
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-prominent);
		box-shadow: var(--shadow-floating);
	}

	h2 {
		margin: 0 0 var(--space-cozy);
		font-size: var(--text-heading);
		font-weight: 600;
		color: var(--color-text);
	}

	p {
		margin: 0 0 var(--space-loose);
		font-size: var(--text-body);
		color: var(--color-subtext);
		line-height: 1.5;
	}

	.actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-cozy);
	}

	.btn {
		padding: var(--space-compact) var(--space-comfortable);
		border: none;
		border-radius: var(--radius-default);
		font-size: var(--text-body);
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.15s;
	}

	.btn.cancel {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.btn.cancel:hover {
		background-color: var(--color-subtext);
	}

	.btn.confirm {
		background-color: var(--color-accent);
		color: var(--color-base);
	}

	.btn.confirm:hover {
		filter: brightness(1.1);
	}

	.btn.confirm.danger {
		background-color: var(--color-error);
	}
</style>
