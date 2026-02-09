import { defineConfig, devices } from '@playwright/test';

const DESKTOP_PORT = 5173;
const MOBILE_PORT = 5174;

export default defineConfig({
	testDir: './e2e',
	outputDir: './screenshots',
	snapshotPathTemplate: '{testDir}/{testFileName}-snapshots/{arg}{ext}',

	expect: {
		toHaveScreenshot: {
			maxDiffPixelRatio: 0.01,
		},
	},

	use: {
		reducedMotion: 'reduce',
	},

	projects: [
		{
			name: 'desktop',
			grep: /Desktop/,
			use: {
				...devices['Desktop Chrome'],
				viewport: { width: 1200, height: 800 },
				baseURL: `http://localhost:${DESKTOP_PORT}`,
			},
		},
		{
			name: 'mobile',
			grep: /Mobile/,
			use: {
				...devices['Desktop Chrome'],
				viewport: { width: 390, height: 844 },
				baseURL: `http://localhost:${MOBILE_PORT}`,
			},
		},
	],

	webServer: [
		{
			command: `VITE_PLATFORM=desktop npx vite dev --port ${DESKTOP_PORT}`,
			port: DESKTOP_PORT,
			reuseExistingServer: !process.env.CI,
		},
		{
			command: `VITE_PLATFORM=mobile npx vite dev --port ${MOBILE_PORT}`,
			port: MOBILE_PORT,
			reuseExistingServer: !process.env.CI,
		},
	],
});
