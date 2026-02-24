/**
 * One-time migration of localStorage keys from plugin prefixes to feature prefixes.
 *
 * Old: basidian-plugin-daily-notes-* → New: basidian-daily-notes-*
 * Old: basidian-plugin-ai-chat-*    → New: basidian-ai-chat-*
 */

const MIGRATIONS: [string, string][] = [
	['basidian-plugin-daily-notes-', 'basidian-daily-notes-'],
	['basidian-plugin-ai-chat-', 'basidian-ai-chat-'],
];

export function migratePluginStorageKeys(): void {
	for (const [oldPrefix, newPrefix] of MIGRATIONS) {
		const keysToMigrate: string[] = [];

		for (let i = 0; i < localStorage.length; i++) {
			const key = localStorage.key(i);
			if (key?.startsWith(oldPrefix)) {
				keysToMigrate.push(key);
			}
		}

		for (const oldKey of keysToMigrate) {
			const suffix = oldKey.slice(oldPrefix.length);
			const newKey = newPrefix + suffix;
			const value = localStorage.getItem(oldKey);
			if (value !== null) {
				localStorage.setItem(newKey, value);
			}
			localStorage.removeItem(oldKey);
		}
	}
}
