import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
	plugins: [svelte({ hot: false })],
	resolve: {
		conditions: ['browser'],
		alias: {
			$lib: path.resolve('./src/lib'),
			'$app/environment': path.resolve('./src/tests/__mocks__/app-environment.ts'),
			'$app/navigation': path.resolve('./src/tests/__mocks__/app-navigation.ts'),
			'$lib/components/CodeMirrorEditor.svelte': path.resolve(
				'./src/tests/__mocks__/CodeMirrorEditor.svelte'
			),
			'$lib/components/MarkdownPreview.svelte': path.resolve(
				'./src/tests/__mocks__/MarkdownPreview.svelte'
			)
		}
	},
	test: {
		environment: 'jsdom',
		globals: true,
		setupFiles: ['./src/tests/setup.ts'],
		include: ['src/tests/**/*.test.ts'],
		env: {
			VITE_PLATFORM: 'desktop'
		}
	}
});
