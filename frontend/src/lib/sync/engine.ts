import { createLogger } from '$lib/utils/logger';
import { pull } from './pull';
import { push } from './push';
import { syncState, syncError, lastSyncAt, refreshPendingCount } from './status';

const log = createLogger('SyncEngine');

const PULL_INTERVAL_MS = 30_000; // 30 seconds
const PUSH_DEBOUNCE_MS = 3_000; // 3 seconds after last local write

let pullTimer: ReturnType<typeof setInterval> | null = null;
let pushTimer: ReturnType<typeof setTimeout> | null = null;
let running = false;

async function runSync(): Promise<void> {
	syncState.set('syncing');
	syncError.set(null);

	try {
		// Pull first, then push
		const serverTime = await pull();
		if (serverTime) {
			lastSyncAt.set(serverTime);
		}

		await push();

		const pending = await refreshPendingCount();
		syncState.set(pending > 0 ? 'pending' : 'synced');
	} catch (e) {
		const message = e instanceof Error ? e.message : 'Sync failed';
		log.warn('sync failed', { error: message });
		syncError.set(message);
		syncState.set('error');
	}
}

export function start(): void {
	if (running) return;
	running = true;

	log.info('sync engine starting');

	// Initial sync immediately
	runSync();

	// Poll for server changes
	pullTimer = setInterval(() => {
		if (running) runSync();
	}, PULL_INTERVAL_MS);
}

export function stop(): void {
	if (!running) return;
	running = false;

	log.info('sync engine stopping');

	if (pullTimer) {
		clearInterval(pullTimer);
		pullTimer = null;
	}
	if (pushTimer) {
		clearTimeout(pushTimer);
		pushTimer = null;
	}
}

export function schedulePush(): void {
	if (pushTimer) clearTimeout(pushTimer);

	pushTimer = setTimeout(async () => {
		pushTimer = null;
		if (!running) return;

		await refreshPendingCount();
		syncState.set('syncing');

		try {
			await push();
			const pending = await refreshPendingCount();
			syncState.set(pending > 0 ? 'pending' : 'synced');
		} catch (e) {
			const message = e instanceof Error ? e.message : 'Push failed';
			log.warn('push failed', { error: message });
			syncError.set(message);
			syncState.set('error');
		}
	}, PUSH_DEBOUNCE_MS);
}

export async function syncNow(): Promise<void> {
	log.info('manual sync triggered');
	await runSync();
}
