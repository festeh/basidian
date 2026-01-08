<script lang="ts">
	import type { FsNode } from '$lib/types';
	import { filesystemActions } from '$lib/stores/filesystem';

	interface Props {
		file: FsNode | null;
	}

	let { file }: Props = $props();

	let content = $state('');
	let hasUnsavedChanges = $state(false);
	let isSaving = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;

	// Sync content when file changes
	$effect(() => {
		if (file) {
			content = file.content || '';
			hasUnsavedChanges = false;
		}
	});

	function handleInput(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		content = target.value;
		hasUnsavedChanges = true;

		// Debounced auto-save
		if (saveTimeout) {
			clearTimeout(saveTimeout);
		}
		saveTimeout = setTimeout(save, 1500);
	}

	async function save() {
		if (!file || !hasUnsavedChanges || isSaving) return;

		isSaving = true;
		try {
			await filesystemActions.updateNode({
				...file,
				content
			});
			hasUnsavedChanges = false;
		} finally {
			isSaving = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if ((e.ctrlKey || e.metaKey) && e.key === 's') {
			e.preventDefault();
			if (saveTimeout) {
				clearTimeout(saveTimeout);
			}
			save();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="editor">
	{#if file}
		<div class="editor-header">
			<span class="filename">
				{file.name}
				{#if hasUnsavedChanges}
					<span class="unsaved-dot" title="Unsaved changes"></span>
				{/if}
			</span>
			{#if isSaving}
				<span class="saving">Saving...</span>
			{/if}
		</div>
		<textarea class="editor-content" value={content} oninput={handleInput} spellcheck="false"
		></textarea>
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
		padding: 12px 16px;
		border-bottom: 1px solid var(--color-overlay);
		background-color: var(--color-surface);
	}

	.filename {
		display: flex;
		align-items: center;
		gap: 8px;
		font-weight: 500;
	}

	.unsaved-dot {
		width: 8px;
		height: 8px;
		background-color: var(--color-secondary);
		border-radius: 50%;
	}

	.saving {
		font-size: 12px;
		color: var(--color-subtext);
	}

	.editor-content {
		flex: 1;
		padding: 16px;
		border: none;
		background: transparent;
		color: var(--color-text);
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		font-size: 14px;
		line-height: 1.6;
		resize: none;
		outline: none;
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
