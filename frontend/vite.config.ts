import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

if (!process.env.VITE_PLATFORM) {
	throw new Error('VITE_PLATFORM environment variable is required (desktop or mobile)');
}

export default defineConfig({
	plugins: [sveltekit()],
	define: {
		__BUILD_TIMESTAMP__: JSON.stringify(new Date().toISOString())
	}
});
