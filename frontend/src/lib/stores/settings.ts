import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'basidian-settings';

export interface Settings {
	vimMode: boolean;
}

const DEFAULT_SETTINGS: Settings = {
	vimMode: false
};

function loadSettings(): Settings {
	if (browser) {
		try {
			const stored = localStorage.getItem(STORAGE_KEY);
			if (stored) {
				return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
			}
		} catch {
			// Ignore parse errors
		}
	}
	return DEFAULT_SETTINGS;
}

function saveSettings(settings: Settings) {
	if (browser) {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
	}
}

function createSettingsStore() {
	const { subscribe, set, update } = writable<Settings>(loadSettings());

	return {
		subscribe,
		update: (updater: (settings: Settings) => Settings) => {
			update((current) => {
				const updated = updater(current);
				saveSettings(updated);
				return updated;
			});
		},
		set: (settings: Settings) => {
			saveSettings(settings);
			set(settings);
		}
	};
}

export const settings = createSettingsStore();
