<script lang="ts">
	import type { FsNode } from '$lib/types';
	import { filesystemActions } from '$lib/stores/filesystem';
	import { createLogger } from '$lib/utils/logger';
	import CodeMirrorEditor from './CodeMirrorEditor.svelte';
	import MarkdownPreview from './MarkdownPreview.svelte';

	const log = createLogger('Editor');

	interface Props {
		file: FsNode | null;
	}

	let { file }: Props = $props();

	let content = $state('');
	let hasUnsavedChanges = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let mode: 'edit' | 'preview' = $state('edit');
	let isRenaming = $state(false);
	let renameValue = $state('');
	let renameInput = $state<HTMLInputElement | null>(null);

	// Sync content when file changes
	$effect(() => {
		if (file) {
			content = file.content || '';
			hasUnsavedChanges = false;
		}
	});

	function handleContentChange(newContent: string) {
		content = newContent;
		hasUnsavedChanges = true;

		// Debounced auto-save (2.5 seconds)
		if (saveTimeout) {
			clearTimeout(saveTimeout);
		}
		saveTimeout = setTimeout(save, 2500);
	}

	async function save() {
		if (!file || !hasUnsavedChanges) return;

		try {
			await filesystemActions.updateNode({
				...file,
				content
			});
			hasUnsavedChanges = false;
		} catch {
			// Keep hasUnsavedChanges true on error
		}
	}

	function startRename() {
		if (!file) return;
		log.debug('startRename', { name: file.name });
		renameValue = file.name;
		isRenaming = true;
		setTimeout(() => renameInput?.select(), 0);
	}

	async function commitRename() {
		log.debug('commitRename', { file: file?.name, isRenaming, renameValue });
		if (!file || !isRenaming) return;
		isRenaming = false;

		const newName = renameValue.trim();
		if (!newName || newName === file.name) {
			log.debug('rename skipped', { reason: !newName ? 'empty' : 'unchanged' });
			return;
		}

		log.info('renaming file', { from: file.name, to: newName });
		await filesystemActions.renameNode(file, newName);
	}

	function handleRenameKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			commitRename();
		} else if (e.key === 'Escape') {
			isRenaming = false;
		}
	}
</script>

<div class="editor">
	{#if file}
		<div class="editor-header">
			<div class="left">
				{#if isRenaming}
					<input
						bind:this={renameInput}
						bind:value={renameValue}
						class="rename-input"
						onblur={commitRename}
						onkeydown={handleRenameKeydown}
					/>
				{:else}
					<button class="filename" onclick={startRename}>
						{file.name}
						{#if hasUnsavedChanges}
							<span class="unsaved-dot" title="Unsaved changes"></span>
						{/if}
					</button>
				{/if}
			</div>
			<div class="mode-toggle">
				<button
					class="toggle-btn"
					class:active={mode === 'edit'}
					onclick={() => (mode = 'edit')}
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
						<path
							d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"
						/>
					</svg>
					Edit
				</button>
				<button
					class="toggle-btn"
					class:active={mode === 'preview'}
					onclick={() => (mode = 'preview')}
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
						<path
							d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
						/>
					</svg>
					Preview
				</button>
			</div>
		</div>
		<div class="editor-body">
			{#if mode === 'edit'}
				<CodeMirrorEditor {content} onchange={handleContentChange} />
			{:else}
				<MarkdownPreview {content} />
			{/if}
		</div>
	{:else}
		<div class="empty-state">
			<svg width="64" height="64" viewBox="0 0 24 24" fill="var(--color-overlay)">
				<path
					d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"
				/>
			</svg>
			<p>Select a file to edit</p>
		</div>
	{/if}
</div>

<style>
	.editor {
		display: flex;
		flex-direction: column;
		flex: 1;
		height: 100%;
		background-color: var(--color-base);
	}

	.editor-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 8px 16px;
		border-bottom: 1px solid var(--color-overlay);
		background-color: var(--color-surface);
	}

	.left {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.filename {
		display: flex;
		align-items: center;
		gap: 8px;
		font-weight: 500;
		background: none;
		border: none;
		color: var(--color-text);
		font-size: inherit;
		padding: 4px 8px;
		margin: -4px -8px;
		border-radius: 4px;
		cursor: pointer;
	}

	.filename:hover {
		background-color: var(--color-overlay);
	}

	.rename-input {
		font-size: inherit;
		font-weight: 500;
		font-family: inherit;
		padding: 4px 8px;
		border: 1px solid var(--color-accent);
		border-radius: 4px;
		background-color: var(--color-base);
		color: var(--color-text);
		outline: none;
	}

	.unsaved-dot {
		width: 8px;
		height: 8px;
		background-color: var(--color-secondary);
		border-radius: 50%;
	}

	.mode-toggle {
		display: flex;
		gap: 4px;
		background-color: var(--color-mantle);
		padding: 4px;
		border-radius: 8px;
	}

	.toggle-btn {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 6px 12px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		font-size: 13px;
		font-weight: 500;
		border-radius: 6px;
		cursor: pointer;
		transition:
			background-color 0.15s,
			color 0.15s;
	}

	.toggle-btn:hover {
		color: var(--color-text);
	}

	.toggle-btn.active {
		background-color: var(--color-surface);
		color: var(--color-text);
	}

	.editor-body {
		flex: 1;
		overflow: hidden;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: 16px;
		color: var(--color-subtext);
	}

	.empty-state p {
		margin: 0;
	}
</style>
