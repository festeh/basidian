<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import TopBar from '$lib/components/TopBar.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Editor from '$lib/components/Editor.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import StatusBar from '$lib/components/StatusBar.svelte';
	import {
		filesystemActions,
		currentFile,
		isLoadingFile,
		selectedNode
	} from '$lib/stores/filesystem';

	let sidebarCollapsed = $state(false);
	let showCreateFileModal = $state(false);
	let showCreateFolderModal = $state(false);
	let newItemName = $state('');
	let isCreating = $state(false);

	onMount(() => {
		filesystemActions.loadTree();
	});

	function toggleSidebar() {
		sidebarCollapsed = !sidebarCollapsed;
	}

	function openSettings() {
		goto('/settings');
	}

	function openInfo() {
		goto('/info');
	}

	function openCreateFileModal() {
		newItemName = '';
		showCreateFileModal = true;
	}

	function openCreateFolderModal() {
		newItemName = '';
		showCreateFolderModal = true;
	}

	async function createFile() {
		if (!newItemName.trim() || isCreating) return;

		isCreating = true;
		const parentPath = $selectedNode?.type === 'folder' ? $selectedNode.path : '/';
		const name = newItemName.endsWith('.md') ? newItemName : `${newItemName}.md`;

		const node = await filesystemActions.createFile(parentPath, name);
		if (node) {
			showCreateFileModal = false;
			await filesystemActions.openFile(node);
		}
		isCreating = false;
	}

	async function createFolder() {
		if (!newItemName.trim() || isCreating) return;

		isCreating = true;
		const parentPath = $selectedNode?.type === 'folder' ? $selectedNode.path : '/';

		await filesystemActions.createFolder(parentPath, newItemName);
		showCreateFolderModal = false;
		isCreating = false;
	}

	function handleModalKeydown(e: KeyboardEvent, action: () => void) {
		if (e.key === 'Enter') {
			action();
		}
	}
</script>

<div class="app">
	<TopBar {sidebarCollapsed} onToggleSidebar={toggleSidebar} onOpenSettings={openSettings} onOpenInfo={openInfo} />
	<div class="divider horizontal"></div>

	<div class="content">
		{#if !sidebarCollapsed}
			<Sidebar onCreateFile={openCreateFileModal} onCreateFolder={openCreateFolderModal} />
		{/if}

		<main class="main">
			{#if $isLoadingFile}
				<div class="loading">
					<div class="spinner"></div>
				</div>
			{:else}
				<Editor file={$currentFile} />
			{/if}
		</main>
	</div>

	<StatusBar />
</div>

<!-- Create File Modal -->
<Modal open={showCreateFileModal} title="New File" onClose={() => (showCreateFileModal = false)}>
	{#snippet children()}
		<input
			type="text"
			class="input"
			placeholder="File name"
			bind:value={newItemName}
			onkeydown={(e) => handleModalKeydown(e, createFile)}
		/>
	{/snippet}
	{#snippet actions()}
		<button class="btn secondary" onclick={() => (showCreateFileModal = false)}>Cancel</button>
		<button class="btn primary" onclick={createFile} disabled={!newItemName.trim() || isCreating}>
			Create
		</button>
	{/snippet}
</Modal>

<!-- Create Folder Modal -->
<Modal
	open={showCreateFolderModal}
	title="New Folder"
	onClose={() => (showCreateFolderModal = false)}
>
	{#snippet children()}
		<input
			type="text"
			class="input"
			placeholder="Folder name"
			bind:value={newItemName}
			onkeydown={(e) => handleModalKeydown(e, createFolder)}
		/>
	{/snippet}
	{#snippet actions()}
		<button class="btn secondary" onclick={() => (showCreateFolderModal = false)}>Cancel</button>
		<button
			class="btn primary"
			onclick={createFolder}
			disabled={!newItemName.trim() || isCreating}
		>
			Create
		</button>
	{/snippet}
</Modal>

<style>
	.app {
		display: flex;
		flex-direction: column;
		height: 100vh;
		padding-top: var(--safe-area-inset-top);
		padding-left: var(--safe-area-inset-left);
		padding-right: var(--safe-area-inset-right);
	}

	.divider.horizontal {
		height: 1px;
		background-color: var(--color-overlay);
	}

	.content {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	.main {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	.loading {
		display: flex;
		align-items: center;
		justify-content: center;
		flex: 1;
	}

	.spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--color-overlay);
		border-top-color: var(--color-accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* Modal form styles */
	:global(.input) {
		width: 100%;
		padding: 12px;
		border: 1px solid var(--color-overlay);
		border-radius: 8px;
		background-color: var(--color-base);
		color: var(--color-text);
		font-size: 14px;
		outline: none;
	}

	:global(.input:focus) {
		border-color: var(--color-accent);
	}

	:global(.btn) {
		padding: 10px 20px;
		border: none;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.15s;
	}

	:global(.btn:disabled) {
		opacity: 0.5;
		cursor: not-allowed;
	}

	:global(.btn.primary) {
		background-color: var(--color-accent);
		color: var(--color-base);
	}

	:global(.btn.primary:hover:not(:disabled)) {
		filter: brightness(1.1);
	}

	:global(.btn.secondary) {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	:global(.btn.secondary:hover:not(:disabled)) {
		background-color: var(--color-subtext);
	}
</style>
