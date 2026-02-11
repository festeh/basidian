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

	function getParentPath(): string {
		const selected = get(selectedNode);
		return selected?.type === 'folder' ? selected.path : '/';
	}

	async function createFile() {
		const trimmed = newItemName.trim();
		if (!trimmed || isCreating) return;

		isCreating = true;
		const name = trimmed.endsWith('.md') ? trimmed : `${trimmed}.md`;
		const node = await filesystemActions.createFile(getParentPath(), name);
		if (node) {
			showCreateFileModal = false;
			await filesystemActions.openFile(node);
		}
		isCreating = false;
	}

	async function createFolder() {
		const trimmed = newItemName.trim();
		if (!trimmed || isCreating) return;

		isCreating = true;
		await filesystemActions.createFolder(getParentPath(), trimmed);
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
