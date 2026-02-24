import { writable } from 'svelte/store';

export interface Notification {
	id: string;
	message: string;
	type: 'info' | 'success' | 'error';
}

const _notifications = writable<Notification[]>([]);

export const notifications = { subscribe: _notifications.subscribe };

export function showNotification(message: string, type: 'info' | 'success' | 'error' = 'info') {
	const id = Date.now().toString();
	_notifications.update((n) => [...n, { id, message, type }]);
	setTimeout(() => {
		_notifications.update((n) => n.filter((item) => item.id !== id));
	}, 5000);
}

export function dismissNotification(id: string) {
	_notifications.update((n) => n.filter((item) => item.id !== id));
}
