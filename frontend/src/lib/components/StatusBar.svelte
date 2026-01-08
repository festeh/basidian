<script lang="ts">
	import PluginSlot from '$lib/plugins/PluginSlot.svelte';
	import { uiRegistry, type Notification } from '$lib/plugins';

	let notifications: Notification[] = $state([]);
	uiRegistry.notifications.subscribe((value) => (notifications = value));
</script>

<div class="status-bar">
	<div class="status-left">
		<PluginSlot slot="statusBar" />
	</div>
	<div class="status-right">
		<!-- Core status items can go here -->
	</div>
</div>

<!-- Notifications -->
{#if notifications.length > 0}
	<div class="notifications">
		{#each notifications as notification (notification.id)}
			<div class="notification notification-{notification.type}">
				<span>{notification.message}</span>
				<button
					class="dismiss"
					onclick={() => uiRegistry.dismissNotification(notification.id)}
				>
					&times;
				</button>
			</div>
		{/each}
	</div>
{/if}

<style>
	.status-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		height: 24px;
		padding: 0 12px;
		background: var(--color-mantle);
		border-top: 1px solid var(--color-surface);
		font-size: 12px;
		color: var(--color-subtext);
	}

	.status-left,
	.status-right {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.notifications {
		position: fixed;
		bottom: 32px;
		right: 16px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		z-index: 1000;
	}

	.notification {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 8px 12px;
		border-radius: 6px;
		background: var(--color-surface);
		border: 1px solid var(--color-overlay);
		color: var(--color-text);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
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
		font-size: 16px;
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
