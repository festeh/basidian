<script lang="ts">
	import type { FsNode } from '$lib/types';
	import { filesystemActions } from '$lib/stores/filesystem';
	import { createLogger } from '$lib/utils/logger';
	import CodeMirrorEditor from './CodeMirrorEditor.svelte';
	import MarkdownPreview from './MarkdownPreview.svelte';
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
			{#if mode === 'edit'}
				<CodeMirrorEditor {content} onchange={handleContentChange} />
			{:else}
				<MarkdownPreview {content} />
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
			<p class="empty-hint">Open a file from the sidebar to start editing</p>
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
</style>
