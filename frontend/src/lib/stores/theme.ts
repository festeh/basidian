import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { ThemeName, Theme } from '$lib/types';
import { themes } from '$lib/themes';

const STORAGE_KEY = 'basidian-theme';
const DEFAULT_THEME: ThemeName = 'catppuccin-mocha';

function getInitialTheme(): ThemeName {
	if (browser) {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored && stored in themes) {
			return stored as ThemeName;
		}
	}
	return DEFAULT_THEME;
}

function createThemeStore() {
	const { subscribe, set } = writable<ThemeName>(getInitialTheme());

	return {
		subscribe,
		set: (themeName: ThemeName) => {
			if (browser) {
				localStorage.setItem(STORAGE_KEY, themeName);
			}
			set(themeName);
		}
	};
}

export const currentThemeName = createThemeStore();
export const currentTheme = derived(currentThemeName, ($name) => themes[$name]);

export function applyTheme(theme: Theme) {
	if (!browser) return;

	const root = document.documentElement;
	root.style.setProperty('--color-base', theme.colors.base);
	root.style.setProperty('--color-mantle', theme.colors.mantle);
	root.style.setProperty('--color-surface', theme.colors.surface);
	root.style.setProperty('--color-overlay', theme.colors.overlay);
	root.style.setProperty('--color-text', theme.colors.text);
	root.style.setProperty('--color-subtext', theme.colors.subtext);
	root.style.setProperty('--color-accent', theme.colors.accent);
	root.style.setProperty('--color-secondary', theme.colors.secondary);
	root.style.setProperty('--color-error', theme.colors.error);
	root.style.setProperty('--color-success', theme.colors.success);

	root.style.colorScheme = theme.isDark ? 'dark' : 'light';
}
