<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import TopBarDesktop from '$lib/components/TopBarDesktop.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Editor from '$lib/components/Editor.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import StatusBar from '$lib/components/StatusBar.svelte';
	import { filesystemActions, currentFile, isLoadingFile } from '$lib/stores/filesystem';
	import { createPageState } from '$lib/page-shared.svelte';

	const page = createPageState();

	let sidebarCollapsed = $state(false);

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
</script>

<div class="app">
	<TopBarDesktop {sidebarCollapsed} onToggleSidebar={toggleSidebar} onOpenSettings={openSettings} onOpenInfo={openInfo} />

	<div class="content">
		<div class="sidebar-wrapper" class:collapsed={sidebarCollapsed}>
			<Sidebar onCreateFile={page.openCreateFileModal} onCreateFolder={page.openCreateFolderModal} />
		</div>

		<main class="main">
			{#if $isLoadingFile}
				<div class="loading">
					<div class="spinner"></div>
				</div>
			{:else}
				{#key $currentFile?.id}
					<div class="editor-fade">
						<Editor file={$currentFile} />
					</div>
				{/key}
			{/if}
		</main>
	</div>

	<StatusBar />
</div>

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

	.sidebar-wrapper {
		width: 280px;
		overflow: hidden;
		transition: width 0.25s ease;
	}

	.sidebar-wrapper.collapsed {
		width: 0;
	}

	.main {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	.editor-fade {
		display: flex;
		flex: 1;
		animation: fade-in 0.15s ease;
	}

	@keyframes fade-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
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
</style>
