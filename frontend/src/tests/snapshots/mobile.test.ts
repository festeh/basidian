import { render } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { rootNodes, currentFile, isLoadingFile, isLoading } from '$lib/stores/filesystem';
import { fakeTree, fakeNote } from '../fixtures';

// Override platform to mobile for this test file
vi.mock('$lib/stores/platform', () => ({
	isMobile: true
}));

// Must import PageMobile after the mock is set up
const { default: PageMobile } = await import('../../routes/PageMobile.svelte');

beforeEach(() => {
	rootNodes.set([]);
	currentFile.set(null);
	isLoadingFile.set(false);
	isLoading.set(false);
});

describe('PageMobile snapshots', () => {
	it('empty state — top bar with hamburger, editor placeholder', () => {
		rootNodes.set([]);
		currentFile.set(null);

		const { container } = render(PageMobile);
		expect(container).toMatchSnapshot();
	});

	it('note open — top bar, editor showing file content', () => {
		rootNodes.set(fakeTree);
		currentFile.set(fakeNote);

		const { container } = render(PageMobile);
		expect(container).toMatchSnapshot();
	});

	it('loading state — spinner shown in editor area', () => {
		rootNodes.set(fakeTree);
		currentFile.set(null);
		isLoadingFile.set(true);

		const { container } = render(PageMobile);
		expect(container).toMatchSnapshot();
	});
});
