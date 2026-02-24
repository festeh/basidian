<script lang="ts">
	import { notifications, dismissNotification, type Notification } from '$lib/stores/notifications';

	let items: Notification[] = $state([]);
	notifications.subscribe((value) => (items = value));
</script>

{#if items.length > 0}
	<div class="notifications">
		{#each items as notification (notification.id)}
			<div class="notification notification-{notification.type}">
				<span>{notification.message}</span>
				<button
					class="dismiss"
					onclick={() => dismissNotification(notification.id)}
				>
					&times;
				</button>
			</div>
		{/each}
	</div>
{/if}

<style>
.notifications {
		position: fixed;
		bottom: calc(32px + var(--safe-area-inset-bottom));
		right: calc(16px + var(--safe-area-inset-right));
		display: flex;
		flex-direction: column;
		gap: var(--space-compact);
		z-index: var(--z-modal);
	}

	.notification {
		display: flex;
		align-items: center;
		gap: var(--space-cozy);
		padding: var(--space-compact) var(--space-cozy);
		border-radius: var(--radius-default);
		background: var(--color-surface);
		border: 1px solid var(--color-overlay);
		color: var(--color-text);
		box-shadow: var(--shadow-subtle);
		animation: slide-in 0.2s ease-out;
	}

	.notification-success {
		border-color: var(--color-success);
	}

	.notification-error {
		border-color: var(--color-error);
	}

	.notification-info {
		border-color: var(--color-accent);
	}

	.dismiss {
		background: none;
		border: none;
		color: var(--color-subtext);
		cursor: pointer;
		padding: 0;
		font-size: var(--text-subheading);
		line-height: 1;
	}

	.dismiss:hover {
		color: var(--color-text);
	}

	@keyframes slide-in {
		from {
			opacity: 0;
			transform: translateX(20px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}
</style>
