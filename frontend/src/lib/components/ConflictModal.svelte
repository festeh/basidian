<script lang="ts">
	import Modal from './Modal.svelte';
	import { conflicts, type SyncConflict } from '$lib/sync/status';
	import { getDb } from '$lib/db/connection';
	import { schedulePush } from '$lib/sync/engine';
	import { filesystemActions } from '$lib/stores/filesystem';
	import { createLogger } from '$lib/utils/logger';

	const log = createLogger('ConflictModal');

	let items: SyncConflict[] = $state([]);
	conflicts.subscribe((v) => (items = v));

	let current = $derived(items[0] ?? null);

	async function keepLocal() {
		if (!current) return;
		log.info('conflict resolved: keeping local version', { id: current.nodeId, path: current.nodePath });

		// Undo the soft delete locally and mark dirty so it pushes back
		const db = await getDb();
		const now = new Date().toISOString();
		await db.execute(
			'UPDATE fs_nodes SET deleted_at = NULL, is_dirty = 1, updated_at = $1 WHERE id = $2',
			[now, current.nodeId]
		);
		await db.execute(
			'UPDATE fs_content SET is_dirty = 1, updated_at = $1 WHERE node_id = $2',
			[now, current.nodeId]
		);

		removeFirst();
		schedulePush();
		await filesystemActions.loadTree();
	}

	async function discardLocal() {
		if (!current) return;
		log.info('conflict resolved: discarding local edits', { id: current.nodeId, path: current.nodePath });

		// Accept the server deletion — soft-delete locally and clear dirty
		const db = await getDb();
		const now = new Date().toISOString();
		await db.execute(
			'UPDATE fs_nodes SET deleted_at = $1, is_dirty = 0 WHERE id = $2',
			[now, current.nodeId]
		);
		await db.execute(
			'UPDATE fs_content SET is_dirty = 0 WHERE node_id = $1',
			[current.nodeId]
		);

		removeFirst();
		await filesystemActions.loadTree();
	}

	function removeFirst() {
		conflicts.update((list) => list.slice(1));
	}
</script>

<Modal open={current !== null} title="Sync Conflict" onClose={discardLocal}>
	{#snippet children()}
		{#if current}
			<div class="conflict-info">
				<p class="conflict-desc">
					<strong>{current.nodeName}</strong> was deleted on the server, but you have local edits.
				</p>
				<p class="conflict-path">{current.nodePath}</p>
				{#if current.localBody}
					<details class="preview">
						<summary>Preview local version</summary>
						<pre class="preview-body">{current.localBody.slice(0, 500)}{current.localBody.length > 500 ? '...' : ''}</pre>
					</details>
				{/if}
			</div>
		{/if}
	{/snippet}
	{#snippet actions()}
		<button class="btn secondary" onclick={discardLocal}>Discard my edits</button>
		<button class="btn primary" onclick={keepLocal}>Keep my version</button>
	{/snippet}
</Modal>

<style>
	.conflict-info {
		display: flex;
		flex-direction: column;
		gap: var(--space-compact);
	}

	.conflict-desc {
		margin: 0;
		line-height: 1.5;
	}

	.conflict-path {
		margin: 0;
		font-size: var(--text-detail);
		color: var(--color-subtext);
		font-family: monospace;
	}

	.preview {
		margin-top: var(--space-compact);
	}

	.preview summary {
		cursor: pointer;
		font-size: var(--text-detail);
		color: var(--color-subtext);
	}

	.preview-body {
		margin: var(--space-compact) 0 0;
		padding: var(--space-compact);
		background: var(--color-mantle);
		border-radius: var(--radius-default);
		font-size: var(--text-detail);
		max-height: 200px;
		overflow: auto;
		white-space: pre-wrap;
		word-break: break-word;
	}
</style>
