import { getDb } from './connection';

export async function getBody(nodeId: string): Promise<string | null> {
	const db = await getDb();
	const rows = await db.select<{ body: string }[]>(
		'SELECT body FROM fs_content WHERE node_id = $1',
		[nodeId]
	);
	return rows.length > 0 ? rows[0].body : null;
}

export async function updateBody(nodeId: string, body: string): Promise<void> {
	const db = await getDb();
	const timestamp = new Date().toISOString();

	await db.execute(
		'UPDATE fs_content SET body = $1, updated_at = $2, is_dirty = 1 WHERE node_id = $3',
		[body, timestamp, nodeId]
	);

	// Keep fs_nodes.updated_at in sync
	await db.execute(
		'UPDATE fs_nodes SET updated_at = $1, is_dirty = 1 WHERE id = $2',
		[timestamp, nodeId]
	);
}
