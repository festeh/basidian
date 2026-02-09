<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import TopBarMobile from '$lib/components/TopBarMobile.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Backdrop from '$lib/components/Backdrop.svelte';
	import Editor from '$lib/components/Editor.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import StatusBar from '$lib/components/StatusBar.svelte';
	import { filesystemActions, currentFile, isLoadingFile } from '$lib/stores/filesystem';
	import { createPageState } from '$lib/page-shared.svelte';

	const page = createPageState();

	let sidebarOpen = $state(false);

	onMount(() => {
		filesystemActions.loadTree();
	});

	// Auto-close sidebar when a file is selected
	$effect(() => {
		if ($currentFile) {
			sidebarOpen = false;
		}
	});

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	function closeSidebar() {
		sidebarOpen = false;
	}

	function openSettings() {
		goto('/settings');
	}

	function openInfo() {
		goto('/info');
	}
</script>

<div class="app">
	<TopBarMobile onToggleSidebar={toggleSidebar} onOpenSettings={openSettings} onOpenInfo={openInfo} />

	<div class="content">
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

<!-- Mobile sidebar overlay -->
{#if sidebarOpen}
	<Backdrop onClose={closeSidebar} />
	<div class="sidebar-overlay">
		<Sidebar onCreateFile={page.openCreateFileModal} onCreateFolder={page.openCreateFolderModal} />
	</div>
{/if}

<!-- Create File Modal -->
<Modal open={page.showCreateFileModal} title="New File" onClose={() => (page.showCreateFileModal = false)}>
	{#snippet children()}
		<input
			type="text"
			class="input"
			placeholder="File name"
			bind:value={page.newItemName}
			onkeydown={(e) => page.handleModalKeydown(e, page.createFile)}
		/>
	{/snippet}
	{#snippet actions()}
		<button class="btn secondary" onclick={() => (page.showCreateFileModal = false)}>Cancel</button>
		<button class="btn primary" onclick={page.createFile} disabled={!page.newItemName.trim() || page.isCreating}>
			Create
		</button>
	{/snippet}
</Modal>

<!-- Create Folder Modal -->
<Modal
	open={page.showCreateFolderModal}
	title="New Folder"
	onClose={() => (page.showCreateFolderModal = false)}
>
	{#snippet children()}
		<input
			type="text"
			class="input"
			placeholder="Folder name"
			bind:value={page.newItemName}
			onkeydown={(e) => page.handleModalKeydown(e, page.createFolder)}
		/>
	{/snippet}
	{#snippet actions()}
		<button class="btn secondary" onclick={() => (page.showCreateFolderModal = false)}>Cancel</button>
		<button
			class="btn primary"
			onclick={page.createFolder}
			disabled={!page.newItemName.trim() || page.isCreating}
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

	.sidebar-overlay {
		position: fixed;
		top: var(--safe-area-inset-top);
		left: var(--safe-area-inset-left);
		bottom: 0;
		width: 280px;
		z-index: 100;
		animation: slide-in 0.2s ease-out;
	}

	@keyframes slide-in {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(0);
		}
	}
</style>
