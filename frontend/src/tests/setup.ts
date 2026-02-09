import { vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

// Mock Tauri window API (TopBarDesktop calls getCurrentWindow() at module level)
vi.mock('@tauri-apps/api/window', () => ({
	getCurrentWindow: () => ({
		startDragging: vi.fn(),
		minimize: vi.fn(),
		toggleMaximize: vi.fn(),
		close: vi.fn()
	})
}));

// Mock Tauri safe-area plugin
vi.mock('tauri-plugin-safe-area-insets', () => ({
	getInsets: vi.fn().mockResolvedValue({ top: 0, right: 0, bottom: 0, left: 0 })
}));

// Mock Tauri fs plugin (used by logger)
vi.mock('@tauri-apps/plugin-fs', () => ({
	writeTextFile: vi.fn(),
	mkdir: vi.fn(),
	exists: vi.fn().mockResolvedValue(true),
	BaseDirectory: { Temp: 'temp' }
}));
