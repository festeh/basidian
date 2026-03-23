import type { FsNode, FsNodeType } from '$lib/types';
import { getDb } from './connection';

interface NodeRow {
	id: string;
	parent_id: string | null;
	type: FsNodeType;
	name: string;
	path: string;
	sort_order: number;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
}

interface NodeWithContentRow extends NodeRow {
	body: string | null;
}

function parentPath(row: { path: string }): string {
	const i = row.path.lastIndexOf('/');
	return i <= 0 ? '/' : row.path.substring(0, i);
}

function toFsNode(row: NodeRow, content?: string | null): FsNode {
	return {
		id: row.id,
		parent_id: row.parent_id,
		type: row.type,
		name: row.name,
		path: row.path,
		parent_path: parentPath(row),
		sort_order: row.sort_order,
		created_at: row.created_at,
		updated_at: row.updated_at,
		content
	};
}

export async function getTree(): Promise<FsNode[]> {
	const db = await getDb();
	const rows = await db.select<NodeRow[]>(
		'SELECT id, parent_id, type, name, path, sort_order, created_at, updated_at, deleted_at FROM fs_nodes WHERE deleted_at IS NULL'
	);
	return rows.map((r) => toFsNode(r));
}

export async function getNode(id: string): Promise<FsNode | null> {
	const db = await getDb();
	const rows = await db.select<NodeWithContentRow[]>(
		`SELECT n.id, n.parent_id, n.type, n.name, n.path, n.sort_order,
				n.created_at, n.updated_at, n.deleted_at, c.body
		 FROM fs_nodes n
		 LEFT JOIN fs_content c ON c.node_id = n.id
		 WHERE n.id = $1 AND n.deleted_at IS NULL`,
		[id]
	);
	if (rows.length === 0) return null;
	return toFsNode(rows[0], rows[0].body);
}

export async function getRecentFiles(limit = 10): Promise<FsNode[]> {
	const db = await getDb();
	const rows = await db.select<NodeRow[]>(
		`SELECT id, parent_id, type, name, path, sort_order, created_at, updated_at, deleted_at
		 FROM fs_nodes
		 WHERE type = 'file' AND deleted_at IS NULL
		 ORDER BY updated_at DESC
		 LIMIT $1`,
		[limit]
	);
	return rows.map((r) => toFsNode(r));
}

export async function searchFiles(query: string): Promise<FsNode[]> {
	const db = await getDb();
	const pattern = `%${query}%`;
	const rows = await db.select<NodeWithContentRow[]>(
		`SELECT n.id, n.parent_id, n.type, n.name, n.path, n.sort_order,
				n.created_at, n.updated_at, n.deleted_at, c.body
		 FROM fs_nodes n
		 LEFT JOIN fs_content c ON c.node_id = n.id
		 WHERE n.deleted_at IS NULL
		   AND (n.name LIKE $1 COLLATE NOCASE OR c.body LIKE $1 COLLATE NOCASE)`,
		[pattern]
	);
	return rows.map((r) => toFsNode(r, r.body));
}

function generateId(): string {
	const bytes = new Uint8Array(8);
	crypto.getRandomValues(bytes);
	return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

function now(): string {
	return new Date().toISOString();
}

export async function createNode(
	type: FsNodeType,
	name: string,
	parentPath: string,
	content = '',
	sortOrder = 0
): Promise<FsNode> {
	const db = await getDb();
	const id = generateId();
	const timestamp = now();
	const path = parentPath === '/' ? `/${name}` : `${parentPath}/${name}`;

	// Find parent_id from parent path
	let parentId: string | null = null;
	if (parentPath !== '/') {
		const parents = await db.select<{ id: string }[]>(
			'SELECT id FROM fs_nodes WHERE path = $1 AND deleted_at IS NULL',
			[parentPath]
		);
		if (parents.length > 0) parentId = parents[0].id;
	}

	await db.execute(
		`INSERT INTO fs_nodes (id, parent_id, type, name, path, sort_order, created_at, updated_at, is_dirty)
		 VALUES ($1, $2, $3, $4, $5, $6, $7, $7, 1)`,
		[id, parentId, type, name, path, sortOrder, timestamp]
	);

	if (type === 'file') {
		await db.execute(
			`INSERT INTO fs_content (node_id, body, updated_at, is_dirty)
			 VALUES ($1, $2, $3, 1)`,
			[id, content, timestamp]
		);
	}

	return {
		id,
		parent_id: parentId,
		type,
		name,
		path,
		parent_path: parentPath,
		content: type === 'file' ? content : undefined,
		sort_order: sortOrder,
		created_at: timestamp,
		updated_at: timestamp
	};
}

export async function updateNode(
	id: string,
	updates: { name?: string; content?: string; sort_order?: number }
): Promise<FsNode | null> {
	const db = await getDb();
	const timestamp = now();

	if (updates.name !== undefined || updates.sort_order !== undefined) {
		const sets: string[] = ['updated_at = $1', 'is_dirty = 1'];
		const params: unknown[] = [timestamp];
		let idx = 2;

		if (updates.name !== undefined) {
			sets.push(`name = $${idx}`);
			params.push(updates.name);
			idx++;
		}
		if (updates.sort_order !== undefined) {
			sets.push(`sort_order = $${idx}`);
			params.push(updates.sort_order);
			idx++;
		}

		params.push(id);
		await db.execute(
			`UPDATE fs_nodes SET ${sets.join(', ')} WHERE id = $${idx}`,
			params
		);
	}

	if (updates.content !== undefined) {
		await db.execute(
			`UPDATE fs_content SET body = $1, updated_at = $2, is_dirty = 1 WHERE node_id = $3`,
			[updates.content, timestamp, id]
		);
		// Keep fs_nodes.updated_at in sync with content changes
		await db.execute(
			'UPDATE fs_nodes SET updated_at = $1, is_dirty = 1 WHERE id = $2',
			[timestamp, id]
		);
	}

	return getNode(id);
}

export async function softDeleteNode(id: string): Promise<void> {
	const db = await getDb();
	const timestamp = now();

	// Soft-delete the node and all descendants
	await db.execute(
		`WITH RECURSIVE descendants AS (
			SELECT id FROM fs_nodes WHERE id = $1
			UNION ALL
			SELECT n.id FROM fs_nodes n JOIN descendants d ON n.parent_id = d.id
		)
		UPDATE fs_nodes SET deleted_at = $2, is_dirty = 1
		WHERE id IN (SELECT id FROM descendants)`,
		[id, timestamp]
	);
}

export async function moveNode(
	id: string,
	newParentPath?: string,
	newName?: string
): Promise<FsNode | null> {
	const db = await getDb();
	const timestamp = now();

	const node = await getNode(id);
	if (!node) return null;

	const name = newName ?? node.name;
	let parentId = node.parent_id;

	if (newParentPath !== undefined) {
		if (newParentPath === '/') {
			parentId = null;
		} else {
			const parents = await db.select<{ id: string }[]>(
				'SELECT id FROM fs_nodes WHERE path = $1 AND deleted_at IS NULL',
				[newParentPath]
			);
			if (parents.length > 0) parentId = parents[0].id;
		}
	}

	const parentPrefix = newParentPath ?? parentPath(node);
	const newPath = parentPrefix === '/' ? `/${name}` : `${parentPrefix}/${name}`;
	const oldPath = node.path;

	await db.execute(
		`UPDATE fs_nodes SET parent_id = $1, name = $2, path = $3, updated_at = $4, is_dirty = 1
		 WHERE id = $5`,
		[parentId, name, newPath, timestamp, id]
	);

	// Update descendant paths
	if (node.type === 'folder') {
		await db.execute(
			`UPDATE fs_nodes
			 SET path = $1 || substr(path, $2),
				 updated_at = $3,
				 is_dirty = 1
			 WHERE path LIKE $4 AND id != $5`,
			[newPath, oldPath.length + 1, timestamp, `${oldPath}/%`, id]
		);
	}

	return getNode(id);
}
