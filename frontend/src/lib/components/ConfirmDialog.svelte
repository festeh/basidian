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
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: rgba(0, 0, 0, 0.5);
	}

	.dialog {
		min-width: 300px;
		max-width: 400px;
		padding: 24px;
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 12px;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
	}

	h2 {
		margin: 0 0 12px;
		font-size: 18px;
		font-weight: 600;
		color: var(--color-text);
	}

	p {
		margin: 0 0 24px;
		font-size: 14px;
		color: var(--color-subtext);
		line-height: 1.5;
	}

	.actions {
		display: flex;
		justify-content: flex-end;
		gap: 12px;
	}

	.btn {
		padding: 8px 16px;
		border: none;
		border-radius: 6px;
		font-size: 14px;
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
