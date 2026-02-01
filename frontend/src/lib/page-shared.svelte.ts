import { filesystemActions, selectedNode } from '$lib/stores/filesystem';
import { get } from 'svelte/store';
import type { FsNode } from '$lib/types';

export function createPageState() {
	let showCreateFileModal = $state(false);
	let showCreateFolderModal = $state(false);
	let newItemName = $state('');
	let isCreating = $state(false);

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
		const selected = get(selectedNode);
		const parentPath = selected?.type === 'folder' ? selected.path : '/';
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
		const selected = get(selectedNode);
		const parentPath = selected?.type === 'folder' ? selected.path : '/';

		await filesystemActions.createFolder(parentPath, newItemName);
		showCreateFolderModal = false;
		isCreating = false;
	}

	function handleModalKeydown(e: KeyboardEvent, action: () => void) {
		if (e.key === 'Enter') {
			action();
		}
	}

	return {
		get showCreateFileModal() { return showCreateFileModal; },
		set showCreateFileModal(v: boolean) { showCreateFileModal = v; },
		get showCreateFolderModal() { return showCreateFolderModal; },
		set showCreateFolderModal(v: boolean) { showCreateFolderModal = v; },
		get newItemName() { return newItemName; },
		set newItemName(v: string) { newItemName = v; },
		get isCreating() { return isCreating; },
		openCreateFileModal,
		openCreateFolderModal,
		createFile,
		createFolder,
		handleModalKeydown
	};
}
