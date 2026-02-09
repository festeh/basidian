import { test, expect, type Page } from '@playwright/test';
import { fakeTreeFlat, fakeNote } from './fixtures';

/** Must match VITE_BACKEND_URL default in $lib/api/client.ts */
const API_BASE = process.env.VITE_BACKEND_URL || 'http://localhost:8090/api';

/**
 * Inject a minimal Tauri runtime stub so the app doesn't crash
 * when importing @tauri-apps/api (TopBarDesktop calls getCurrentWindow()).
 */
async function mockTauri(page: Page) {
	await page.addInitScript(() => {
		// @ts-expect-error — injecting stub into browser global
		window.__TAURI_INTERNALS__ = {
			metadata: { currentWindow: { label: 'main' }, currentWebview: { label: 'main' } },
			invoke: () => Promise.resolve(),
			convertFileSrc: (s) => s,
			transformCallback: () => 0,
		};
	});
}

/**
 * Intercept all backend API calls so the app works without a real backend.
 * Uses string patterns derived from API_BASE to target the backend only
 * (avoids catching Vite module imports like @tauri-apps/api).
 */
async function mockApi(page: Page) {
	// Catch-all first — in Playwright, later routes take priority over earlier ones,
	// so specific routes registered after this one will override it.
	await page.route(`${API_BASE}/**`, (route) =>
		route.fulfill({ status: 200, json: {} }),
	);

	await page.route(`${API_BASE}/fs/tree**`, (route) =>
		route.fulfill({ json: fakeTreeFlat }),
	);

	await page.route(`${API_BASE}/fs/node/**`, (route) =>
		route.fulfill({ json: fakeNote }),
	);
}

/**
 * Expand the "Projects" folder so files are visible,
 * then wait for the tree items to appear.
 */
async function expandProjectsFolder(page: Page) {
	const projectsFolder = page.locator('button.item-row', { hasText: 'Projects' });
	await projectsFolder.click();
	await page.locator('button.item-row', { hasText: 'Meeting Notes.md' }).waitFor();
}

/** Click a file in the tree to open it, then wait for editor content. */
async function openMeetingNotes(page: Page) {
	await page.locator('button.item-row', { hasText: 'Meeting Notes.md' }).click();
	// Wait for the editor to render the file content
	await page.locator('.cm-editor, .editor').first().waitFor();
}

// ---------------------------------------------------------------------------
// Desktop tests (matched by "desktop" project grep: /Desktop/)
// ---------------------------------------------------------------------------

test.describe('Desktop', () => {
	test.beforeEach(async ({ page }) => {
		await mockTauri(page);
		await mockApi(page);
		await page.goto('/');
		// Wait for the file tree to load (sidebar with tree items)
		await page.locator('.file-tree').waitFor();
		await page.locator('button.item-row').first().waitFor();
	});

	test('empty state — sidebar with tree, no file open', async ({ page }) => {
		await expandProjectsFolder(page);
		await expect(page).toHaveScreenshot('desktop-empty.png');
	});

	test('note open — editor showing file', async ({ page }) => {
		await expandProjectsFolder(page);
		await openMeetingNotes(page);
		await expect(page).toHaveScreenshot('desktop-note.png');
	});

	test('sidebar collapsed — editor only', async ({ page }) => {
		await expandProjectsFolder(page);
		await openMeetingNotes(page);
		// Click the sidebar toggle button
		await page.locator('button[title="Hide sidebar"]').click();
		// Sidebar should be gone
		await expect(page.locator('.sidebar')).not.toBeVisible();
		await expect(page).toHaveScreenshot('desktop-sidebar-collapsed.png');
	});
});

// ---------------------------------------------------------------------------
// Mobile tests (matched by "mobile" project grep: /Mobile/)
// ---------------------------------------------------------------------------

test.describe('Mobile', () => {
	test.beforeEach(async ({ page }) => {
		await mockTauri(page);
		await mockApi(page);
		await page.goto('/');
		// On mobile, sidebar is hidden by default. Wait for the top bar.
		await page.locator('[role="banner"]').waitFor();
	});

	test('empty state — top bar, no file open', async ({ page }) => {
		await expect(page).toHaveScreenshot('mobile-empty.png');
	});

	test('note open — editor showing file', async ({ page }) => {
		// Open hamburger menu to access sidebar
		await page.locator('button[title="Menu"]').click();
		await page.locator('.sidebar-overlay').waitFor();
		await expandProjectsFolder(page);
		await openMeetingNotes(page);
		// Sidebar auto-closes when a file is selected
		await expect(page.locator('.sidebar-overlay')).not.toBeVisible();
		await expect(page).toHaveScreenshot('mobile-note.png');
	});

	test('sidebar overlay visible', async ({ page }) => {
		// Open hamburger menu
		await page.locator('button[title="Menu"]').click();
		await page.locator('.sidebar-overlay').waitFor();
		await expandProjectsFolder(page);
		await expect(page).toHaveScreenshot('mobile-sidebar.png');
	});
});
