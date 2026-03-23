import { writable, derived } from 'svelte/store';
import { getDb } from '$lib/db/connection';

export type SyncState = 'uninitialized' | 'synced' | 'pending' | 'syncing' | 'error';

export interface SyncConflict {
	nodeId: string;
	nodeName: string;
	nodePath: string;
	type: 'deleted_on_server';
	localBody: string;
}

export const conflicts = writable<SyncConflict[]>([]);

export const syncState = writable<SyncState>('uninitialized');
export const syncError = writable<string | null>(null);
export const lastSyncAt = writable<string | null>(null);
export const pendingCount = writable<number>(0);

export const syncSummary = derived(
	[syncState, pendingCount, syncError],
	([$state, $count, $error]) => {
		switch ($state) {
			case 'uninitialized':
				return 'Not synced';
			case 'synced':
				return 'Synced';
			case 'pending':
				return `${$count} unsynced`;
			case 'syncing':
				return 'Syncing...';
			case 'error':
				return $error ?? 'Sync error';
		}
	}
);

export async function refreshPendingCount(): Promise<number> {
	try {
		const db = await getDb();
		const nodeResult = await db.select<{ count: number }[]>(
			'SELECT COUNT(*) as count FROM fs_nodes WHERE is_dirty = 1'
		);
		const contentResult = await db.select<{ count: number }[]>(
			'SELECT COUNT(*) as count FROM fs_content WHERE is_dirty = 1'
		);
		const count = (nodeResult[0]?.count ?? 0) + (contentResult[0]?.count ?? 0);
		pendingCount.set(count);
		return count;
	} catch {
		return 0;
	}
}
