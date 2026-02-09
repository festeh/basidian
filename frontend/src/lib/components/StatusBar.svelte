<script lang="ts">
	import PluginSlot from '$lib/plugins/PluginSlot.svelte';
	import { uiRegistry, type Notification, type UISlotItem } from '$lib/plugins';

	let notifications: Notification[] = $state([]);
	let statusBarItems: UISlotItem[] = $state([]);
	uiRegistry.notifications.subscribe((value) => (notifications = value));
	uiRegistry.statusBarItems.subscribe((value) => (statusBarItems = value));

	const hasContent = $derived(statusBarItems.length > 0);
</script>

{#if hasContent}
<div class="status-bar">
	<div class="status-left">
		<PluginSlot slot="statusBar" />
	</div>
	<div class="status-right">
		<!-- Core status items can go here -->
	</div>
</div>
{/if}

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
		min-height: 24px;
		padding: 0 12px;
		padding-bottom: var(--safe-area-inset-bottom);
		background: var(--color-base);
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
		bottom: calc(32px + var(--safe-area-inset-bottom));
		right: calc(16px + var(--safe-area-inset-right));
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
