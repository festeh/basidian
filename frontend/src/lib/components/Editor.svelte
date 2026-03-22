<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { FsNode } from '$lib/types';
	import { filesystemActions } from '$lib/stores/filesystem';
	import { historyActions, historyOpen } from '$lib/stores/history';
	import { api } from '$lib/api/client';
	import { createLogger } from '$lib/utils/logger';
	import CodeMirrorEditor from './CodeMirrorEditor.svelte';
	import MarkdownPreview from './MarkdownPreview.svelte';
	import HistoryPanel from './HistoryPanel.svelte';
	import TopBar from './TopBar.svelte';

	const log = createLogger('Editor');

	interface Props {
		file: FsNode | null;
		sidebarCollapsed?: boolean;
		onToggleSidebar?: () => void;
		onOpenSettings?: () => void;
		onOpenInfo?: () => void;
	}

	let { file, sidebarCollapsed = false, onToggleSidebar, onOpenSettings, onOpenInfo }: Props = $props();

	let content = $state('');
	let hasUnsavedChanges = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let pendingSave: { file: FsNode; content: string } | null = null;
	let mode: 'edit' | 'preview' = $state('edit');
	let recentFiles = $state<FsNode[]>([]);
	let isRenaming = $state(false);
	let renameValue = $state('');
	let renameInput = $state<HTMLInputElement | null>(null);

	// Flush pending save immediately, then snapshot for version history
	async function flushAndSnapshot(fileId?: string) {
		if (saveTimeout) {
			clearTimeout(saveTimeout);
			saveTimeout = null;
		}
		if (pendingSave) {
			const { file: targetFile, content: targetContent } = pendingSave;
			pendingSave = null;
			await filesystemActions.updateNode({ ...targetFile, content: targetContent });
			if (targetFile.id) {
				api.snapshot(targetFile.id);
			}
		} else if (fileId) {
			// No pending save, but still snapshot (autosave may have already persisted)
			api.snapshot(fileId);
		}
	}

	// Load recent files for the greeting screen
	$effect(() => {
		if (!file) {
			api.getRecentFiles(8).then((files) => {
				recentFiles = files;
			}).catch(() => {
				recentFiles = [];
			});
		}
	});

	// Sync content when file changes
	let previousFileId: string | undefined;
	$effect(() => {
		if (file) {
			// Flush any pending save for the previous file before switching
			flushAndSnapshot(previousFileId);
			historyActions.close();
			previousFileId = file.id;
			content = file.content || '';
			hasUnsavedChanges = false;
		}
	});

	// Clean up on component destroy (handles {#key} remounting)
	onDestroy(() => {
		flushAndSnapshot(file?.id);
	});

	function handleContentChange(newContent: string) {
		content = newContent;
		hasUnsavedChanges = true;

		// Capture current file so the save always targets the correct note
		if (file) {
			pendingSave = { file: { ...file }, content: newContent };
		}

		// Debounced auto-save (2.5 seconds)
		if (saveTimeout) {
			clearTimeout(saveTimeout);
		}
		saveTimeout = setTimeout(save, 2500);
	}

	async function save() {
		if (!pendingSave) return;

		const { file: targetFile, content: targetContent } = pendingSave;
		pendingSave = null;
		saveTimeout = null;

		try {
			await filesystemActions.updateNode({ ...targetFile, content: targetContent });
			// Only clear indicator if still viewing the same file
			if (file?.id === targetFile.id) {
				hasUnsavedChanges = false;
			}
		} catch {
			// Restore pending save on error if still on same file
			if (file?.id === targetFile.id) {
				pendingSave = { file: targetFile, content: targetContent };
			}
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
				{#if onToggleSidebar}
					<button
						class="toggle-sidebar-btn"
						onclick={onToggleSidebar}
						title={sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
					>
						{#if sidebarCollapsed}
							<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
								<path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
							</svg>
						{:else}
							<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
								<path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
							</svg>
						{/if}
					</button>
				{/if}
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
			<div class="right">
				<button
					class="icon-btn"
					class:active={$historyOpen}
					onclick={() => $historyOpen ? historyActions.close() : historyActions.open()}
					title="Version history"
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
						<path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z" />
					</svg>
				</button>
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
				{#if onOpenInfo && onOpenSettings}
					<TopBar {onOpenSettings} {onOpenInfo} />
				{/if}
			</div>
		</div>
		<div class="editor-body">
			<div class="editor-content" class:with-history={$historyOpen}>
				{#if mode === 'edit'}
					<CodeMirrorEditor {content} onchange={handleContentChange} />
				{:else}
					<MarkdownPreview {content} />
				{/if}
			</div>
			{#if $historyOpen}
				<HistoryPanel currentContent={content} />
			{/if}
		</div>
	{:else}
		{#if onOpenInfo || onOpenSettings}
			<div class="editor-header empty-header">
				<div class="left">
					{#if onToggleSidebar}
						<button
							class="toggle-sidebar-btn"
							onclick={onToggleSidebar}
							title={sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
						>
							{#if sidebarCollapsed}
								<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
									<path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
								</svg>
							{:else}
								<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
									<path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
								</svg>
							{/if}
						</button>
					{/if}
				</div>
				<div class="header-actions">
					{#if onOpenInfo && onOpenSettings}
						<TopBar {onOpenSettings} {onOpenInfo} />
					{/if}
				</div>
			</div>
		{/if}
		<div class="empty-state">
			<div class="node-graph">
				<svg width="180" height="140" viewBox="0 0 180 140">
					<line x1="90" y1="50" x2="40" y2="100" stroke="var(--color-overlay)" stroke-width="1.5" />
					<line x1="90" y1="50" x2="140" y2="100" stroke="var(--color-overlay)" stroke-width="1.5" />
					<line x1="90" y1="50" x2="90" y2="20" stroke="var(--color-overlay)" stroke-width="1.5" />
					<line x1="40" y1="100" x2="140" y2="100" stroke="var(--color-overlay)" stroke-width="1.5" stroke-dasharray="4 4" />
					<circle cx="90" cy="50" r="8" fill="var(--color-accent)" class="node node-center" />
					<circle cx="40" cy="100" r="6" fill="var(--color-secondary)" class="node node-left" />
					<circle cx="140" cy="100" r="6" fill="var(--color-secondary)" class="node node-right" />
					<circle cx="90" cy="20" r="5" fill="var(--color-accent)" class="node node-top" opacity="0.6" />
				</svg>
			</div>
			<p class="empty-title">Your knowledge awaits</p>
			{#if recentFiles.length > 0}
				<div class="recent-files">
					<p class="recent-label">Recent files</p>
					<ul class="recent-list">
						{#each recentFiles as recentFile (recentFile.id)}
							<li>
								<button
									class="recent-item"
									onclick={() => filesystemActions.openFile(recentFile)}
								>
									<svg class="recent-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
										<path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z" />
									</svg>
									<span class="recent-name">{recentFile.name}</span>
									<span class="recent-path">{recentFile.parent_path === '/' ? '' : recentFile.parent_path}</span>
								</button>
							</li>
						{/each}
					</ul>
				</div>
			{:else}
				<p class="empty-hint">Open a file from the sidebar to start editing</p>
			{/if}
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
		padding: var(--space-compact) var(--space-comfortable);
		background-color: var(--color-base);
		z-index: var(--z-raised);
	}

	.left,
	.right {
		display: flex;
		align-items: center;
		gap: var(--space-compact);
	}

	.toggle-sidebar-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		border-radius: var(--radius-default);
		cursor: pointer;
	}

	.toggle-sidebar-btn:hover {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.filename {
		display: flex;
		align-items: center;
		gap: var(--space-compact);
		font-weight: 500;
		background: none;
		border: none;
		color: var(--color-text);
		font-size: inherit;
		padding: var(--space-tight) var(--space-compact);
		margin: calc(-1 * var(--space-tight)) calc(-1 * var(--space-compact));
		border-radius: var(--radius-subtle);
		cursor: pointer;
	}

	.filename:hover {
		background-color: var(--color-overlay);
	}

	.rename-input {
		font-size: inherit;
		font-weight: 500;
		font-family: inherit;
		padding: var(--space-tight) var(--space-compact);
		border: 1px solid var(--color-accent);
		border-radius: var(--radius-subtle);
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
		gap: var(--space-tight);
		background-color: var(--color-mantle);
		padding: var(--space-tight);
		border-radius: var(--radius-rounded);
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: var(--space-tight);
		margin-left: var(--space-compact);
	}

	.toggle-btn {
		display: flex;
		align-items: center;
		gap: var(--space-snug);
		padding: var(--space-snug) var(--space-cozy);
		border: none;
		background: transparent;
		color: var(--color-subtext);
		font-size: var(--text-detail);
		font-weight: 500;
		border-radius: var(--radius-default);
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

	.icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		border-radius: var(--radius-default);
		cursor: pointer;
	}

	.icon-btn:hover {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.icon-btn.active {
		color: var(--color-accent);
	}

	.editor-body {
		flex: 1;
		overflow: hidden;
		display: flex;
	}

	.editor-content {
		flex: 1;
		overflow: hidden;
	}

	.editor-content.with-history {
		flex: 1;
		min-width: 0;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: var(--space-cozy);
		color: var(--color-subtext);
	}

	.node-graph {
		margin-bottom: var(--space-compact);
	}

	.node {
		animation: float 4s ease-in-out infinite;
	}

	.node-center {
		animation-delay: 0s;
	}

	.node-left {
		animation-delay: -1s;
	}

	.node-right {
		animation-delay: -2s;
	}

	.node-top {
		animation-delay: -3s;
	}

	@keyframes float {
		0%, 100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-4px);
		}
	}

	.empty-title {
		font-size: var(--text-heading);
		font-weight: 600;
		color: var(--color-text);
		margin: 0;
	}

	.empty-hint {
		font-size: var(--text-detail);
		margin: 0;
	}

	.recent-files {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-compact);
		margin-top: var(--space-compact);
		width: 100%;
		max-width: 320px;
	}

	.recent-label {
		font-size: var(--text-detail);
		color: var(--color-subtext);
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 500;
	}

	.recent-list {
		list-style: none;
		margin: 0;
		padding: 0;
		width: 100%;
	}

	.recent-item {
		display: flex;
		align-items: center;
		gap: var(--space-compact);
		width: 100%;
		padding: var(--space-compact) var(--space-cozy);
		border: none;
		background: transparent;
		color: var(--color-text);
		font-size: var(--text-body);
		font-family: inherit;
		border-radius: var(--radius-default);
		cursor: pointer;
		text-align: left;
	}

	.recent-item:hover {
		background-color: var(--color-overlay);
	}

	.recent-icon {
		flex-shrink: 0;
		color: var(--color-subtext);
	}

	.recent-name {
		flex-shrink: 0;
		font-weight: 500;
	}

	.recent-path {
		color: var(--color-subtext);
		font-size: var(--text-detail);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
