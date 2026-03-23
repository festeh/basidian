import { getDb } from '$lib/db/connection';
import { createLogger } from '$lib/utils/logger';
import { pushChanges } from './client';
import type { SyncNodeRow, SyncContentRow } from './types';

const log = createLogger('SyncPush');

interface DirtyNodeRow {
	id: string;
	parent_id: string | null;
	type: string;
	name: string;
	path: string;
	sort_order: number;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
}

interface DirtyContentRow {
	node_id: string;
	body: string;
	updated_at: string;
}

export async function push(): Promise<void> {
	const db = await getDb();

	// Find dirty nodes
	const dirtyNodes = await db.select<DirtyNodeRow[]>(
		`SELECT id, parent_id, type, name, path, sort_order, created_at, updated_at, deleted_at
		 FROM fs_nodes WHERE is_dirty = 1`
	);

	// Find dirty content
	const dirtyContent = await db.select<DirtyContentRow[]>(
		`SELECT node_id, body, updated_at
		 FROM fs_content WHERE is_dirty = 1`
	);

	if (dirtyNodes.length === 0 && dirtyContent.length === 0) {
		log.debug('nothing to push');
		return;
	}

	log.info('pushing changes', {
		nodes: dirtyNodes.length,
		content: dirtyContent.length
	});

	const nodes: SyncNodeRow[] = dirtyNodes.map((r) => ({
		id: r.id,
		parent_id: r.parent_id,
		type: r.type,
		name: r.name,
		path: r.path,
		sort_order: r.sort_order,
		created_at: r.created_at,
		updated_at: r.updated_at,
		deleted_at: r.deleted_at
	}));

	const content: SyncContentRow[] = dirtyContent.map((r) => ({
		node_id: r.node_id,
		body: r.body,
		updated_at: r.updated_at
	}));

	const response = await pushChanges(nodes, content);

	// Clear dirty flags for accepted rows
	let accepted = 0;
	let rejected = 0;
	for (const result of response.results) {
		if (result.accepted) {
			accepted++;
			// Clear dirty flag — check both tables
			await db.execute('UPDATE fs_nodes SET is_dirty = 0 WHERE id = $1', [result.id]);
			await db.execute('UPDATE fs_content SET is_dirty = 0 WHERE node_id = $1', [result.id]);
		} else {
			rejected++;
			// Server has a newer version — clear dirty flag so the next pull overwrites
			log.warn('push rejected', {
				id: result.id,
				reason: result.reason,
				server_updated_at: result.server_updated_at
			});
			await db.execute('UPDATE fs_nodes SET is_dirty = 0 WHERE id = $1', [result.id]);
			await db.execute('UPDATE fs_content SET is_dirty = 0 WHERE node_id = $1', [result.id]);
		}
	}

	log.info('push complete', { accepted, rejected });
}
