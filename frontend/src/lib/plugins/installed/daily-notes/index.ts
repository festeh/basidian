import type { Plugin, PluginContext } from '../../types';
import type { FsNode } from '$lib/types';
import { get } from 'svelte/store';
import DailyNoteButton from './DailyNoteButton.svelte';

export interface DailyNotesSettings {
	folder: string;
	dateFormat: string;
	templatePath: string;
}

const DEFAULT_SETTINGS: DailyNotesSettings = {
	folder: '/daily',
	dateFormat: 'YYYY-MM-DD',
	templatePath: ''
};

let ctx: PluginContext | null = null;
let unregisterSidebarAction: (() => void) | null = null;

export function getSettings(): DailyNotesSettings {
	if (!ctx) return DEFAULT_SETTINGS;
	const stored = ctx.storage.get<DailyNotesSettings>('settings');
	return { ...DEFAULT_SETTINGS, ...stored };
}

export function saveSettings(settings: DailyNotesSettings): void {
	ctx?.storage.set('settings', settings);
}

export function formatDate(date: Date, format: string = 'YYYY-MM-DD'): string {
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');

	return format
		.replace('YYYY', String(year))
		.replace('MM', month)
		.replace('DD', day);
}

export function parseDate(filename: string): Date | null {
	// Try to parse YYYY-MM-DD from filename
	const match = filename.match(/(\d{4})-(\d{2})-(\d{2})/);
	if (match) {
		return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
	}
	return null;
}

export function getDailyPath(date: Date): string {
	const settings = getSettings();
	const dateStr = formatDate(date, settings.dateFormat);
	return `${settings.folder}/${dateStr}.md`;
}

function findNodeByPath(path: string): FsNode | null {
	if (!ctx) return null;
	const rootNodes = get(ctx.stores.filesystem.rootNodes);

	function searchTree(nodes: FsNode[]): FsNode | null {
		for (const node of nodes) {
			if (node.path === path) return node;
			if (node.children) {
				const found = searchTree(node.children);
				if (found) return found;
			}
		}
		return null;
	}

	return searchTree(rootNodes);
}

async function getTemplateContent(): Promise<string> {
	const settings = getSettings();
	if (!settings.templatePath || !ctx) {
		// Default template with today's date
		const today = new Date();
		return `# ${formatDate(today, settings.dateFormat)}\n\n`;
	}

	// Try to load template file
	const templateNode = findNodeByPath(settings.templatePath);
	if (templateNode?.content) {
		// Replace {{date}} placeholder with today's date
		return templateNode.content.replace(/\{\{date\}\}/g, formatDate(new Date(), settings.dateFormat));
	}

	return `# ${formatDate(new Date(), settings.dateFormat)}\n\n`;
}

export async function openOrCreateDaily(date: Date): Promise<void> {
	if (!ctx) return;

	const settings = getSettings();
	const dateStr = formatDate(date, settings.dateFormat);
	const filename = `${dateStr}.md`;
	const fullPath = `${settings.folder}/${filename}`;

	ctx.log.info(`Opening daily note: ${fullPath}`);

	// Check if exists
	const existing = findNodeByPath(fullPath);
	if (existing) {
		await ctx.actions.filesystem.openFile(existing);
		return;
	}

	// Ensure folder exists - check if folder node exists
	const folderNode = findNodeByPath(settings.folder);
	if (!folderNode) {
		// Create the folder first
		ctx.log.info(`Creating folder: ${settings.folder}`);
		await ctx.actions.filesystem.createFolder('/', settings.folder.replace(/^\//, ''));
		await ctx.actions.filesystem.loadTree();
	}

	// Create the daily note
	const content = await getTemplateContent();
	const node = await ctx.actions.filesystem.createFile(settings.folder, filename, content);

	if (node) {
		await ctx.actions.filesystem.openFile(node);
		ctx.ui.showNotification(`Created daily note: ${dateStr}`, 'success');
	}
}

export function getDailyNotesForMonth(year: number, month: number): Set<number> {
	if (!ctx) return new Set();

	const settings = getSettings();
	const rootNodes = get(ctx.stores.filesystem.rootNodes);
	const days = new Set<number>();

	// Find the daily notes folder
	function findFolder(nodes: FsNode[]): FsNode | null {
		for (const node of nodes) {
			if (node.path === settings.folder && node.type === 'folder') {
				return node;
			}
			if (node.children) {
				const found = findFolder(node.children);
				if (found) return found;
			}
		}
		return null;
	}

	const folder = findFolder(rootNodes);
	if (!folder?.children) return days;

	// Check each file in the folder
	for (const file of folder.children) {
		if (file.type !== 'file') continue;
		const date = parseDate(file.name);
		if (date && date.getFullYear() === year && date.getMonth() === month) {
			days.add(date.getDate());
		}
	}

	return days;
}

export function todayExists(): boolean {
	const todayPath = getDailyPath(new Date());
	return findNodeByPath(todayPath) !== null;
}

const plugin: Plugin = {
	async onLoad(context: PluginContext) {
		ctx = context;
		ctx.log.info('Daily Notes plugin loaded!');

		// Register sidebar action button (includes calendar popup)
		unregisterSidebarAction = ctx.ui.registerSidebarAction(DailyNoteButton);
	},

	async onUnload(context: PluginContext) {
		context.log.info('Daily Notes plugin unloading...');
		unregisterSidebarAction?.();
		ctx = null;
	}
};

export default plugin;
