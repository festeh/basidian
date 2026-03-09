import { writable, get } from 'svelte/store';
import type { FileVersion, FileVersionSummary } from '$lib/types';
import { api } from '$lib/api/client';
import { currentFile } from './filesystem';

export const versions = writable<FileVersionSummary[]>([]);
export const selectedVersion = writable<FileVersion | null>(null);
export const historyOpen = writable(false);
export const historyLoading = writable(false);

export const historyActions = {
	async open() {
		const file = get(currentFile);
		if (!file?.id) return;

		historyOpen.set(true);
		historyLoading.set(true);
		try {
			const list = await api.getVersions(file.id);
			versions.set(list);
		} catch {
			versions.set([]);
		} finally {
			historyLoading.set(false);
		}
	},

	close() {
		historyOpen.set(false);
		selectedVersion.set(null);
		versions.set([]);
	},

	async selectVersion(versionId: string) {
		const file = get(currentFile);
		if (!file?.id) return;

		const version = await api.getVersion(file.id, versionId);
		selectedVersion.set(version);
	},

	async restore(versionId: string) {
		const file = get(currentFile);
		if (!file?.id) return;

		const restored = await api.restoreVersion(file.id, versionId);
		// Update the current file content
		currentFile.update((f) => (f ? { ...f, content: restored.content } : f));
		// Reload version list
		const list = await api.getVersions(file.id);
		versions.set(list);
		selectedVersion.set(null);
	}
};
