import { render } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import { rootNodes, currentFile, isLoadingFile, isLoading } from '$lib/stores/filesystem';
import PageDesktop from '../../routes/PageDesktop.svelte';
import { fakeTree, fakeNote } from '../fixtures';

beforeEach(() => {
	// Reset stores to clean state
	rootNodes.set([]);
	currentFile.set(null);
	isLoadingFile.set(false);
	isLoading.set(false);
});

describe('PageDesktop snapshots', () => {
	it('empty state — sidebar with no files, editor placeholder', () => {
		rootNodes.set([]);
		currentFile.set(null);

		const { container } = render(PageDesktop);
		expect(container).toMatchSnapshot();
	});

	it('note open — sidebar with file tree, editor showing file', () => {
		rootNodes.set(fakeTree);
		currentFile.set(fakeNote);

		const { container } = render(PageDesktop);
		expect(container).toMatchSnapshot();
	});

	it('loading state — spinner shown in editor area', () => {
		rootNodes.set(fakeTree);
		currentFile.set(null);
		isLoadingFile.set(true);

		const { container } = render(PageDesktop);
		expect(container).toMatchSnapshot();
	});
});
