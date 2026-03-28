/**
 * Daily Notes - Shared State
 */

import type { FsNode } from "$lib/types";
import { get } from "svelte/store";
import { rootNodes, filesystemActions } from "$lib/stores/filesystem";
import { createLogger } from "$lib/utils/logger";
import { showNotification } from "$lib/stores/notifications";

const log = createLogger("DailyNotes");

export interface DailyNotesSettings {
  folder: string;
  templatePath: string;
}

const DATE_FORMAT = "DD-MMM-YYYY";

const DEFAULT_SETTINGS: DailyNotesSettings = {
  folder: "/daily",
  templatePath: "",
};

const STORAGE_PREFIX = "basidian-daily-notes-";

function storageGet<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function storageSet<T>(key: string, value: T): void {
  localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
}

export function getSettings(): DailyNotesSettings {
  const stored = storageGet<DailyNotesSettings>("settings");
  return { ...DEFAULT_SETTINGS, ...stored };
}

export function saveSettings(settings: DailyNotesSettings): void {
  storageSet("settings", settings);
}

const MONTH_ABBREVS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function formatDate(date: Date, format: string = DATE_FORMAT): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return format
    .replace("YYYY", String(year))
    .replace("YY", String(year).slice(-2))
    .replace("MMM", MONTH_ABBREVS[date.getMonth()])
    .replace("MM", month)
    .replace("DD", day);
}

export function parseDate(filename: string): Date | null {
  // Try DD-MMM-YYYY format (e.g. 05-Jan-2026)
  const mmmMatch = filename.match(
    /(\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{4})/,
  );
  if (mmmMatch) {
    const monthIdx = MONTH_ABBREVS.indexOf(mmmMatch[2]);
    return new Date(parseInt(mmmMatch[3]), monthIdx, parseInt(mmmMatch[1]));
  }
  // Fallback: try DD-MMM-YY (legacy)
  const yyMatch = filename.match(
    /(\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2})/,
  );
  if (yyMatch) {
    const monthIdx = MONTH_ABBREVS.indexOf(yyMatch[2]);
    const year = 2000 + parseInt(yyMatch[3]);
    return new Date(year, monthIdx, parseInt(yyMatch[1]));
  }
  // Fallback: try YYYY-MM-DD
  const match = filename.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    return new Date(
      parseInt(match[1]),
      parseInt(match[2]) - 1,
      parseInt(match[3]),
    );
  }
  return null;
}

export function getDailyPath(date: Date): string {
  const settings = getSettings();
  const dateStr = formatDate(date);
  return `${settings.folder}/${dateStr}.md`;
}

function findNodeByPath(path: string): FsNode | null {
  const nodes = get(rootNodes);

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

  return searchTree(nodes);
}

async function getTemplateContent(): Promise<string> {
  const settings = getSettings();
  if (!settings.templatePath) {
    const today = new Date();
    return `# ${formatDate(today)}\n\n`;
  }

  const templateNode = findNodeByPath(settings.templatePath);
  if (templateNode?.content) {
    return templateNode.content.replace(
      /\{\{date\}\}/g,
      formatDate(new Date()),
    );
  }

  return `# ${formatDate(new Date())}\n\n`;
}

export async function openOrCreateDaily(date: Date): Promise<void> {
  const settings = getSettings();
  const dateStr = formatDate(date);
  const filename = `${dateStr}.md`;
  const fullPath = `${settings.folder}/${filename}`;

  log.info(`Opening daily note: ${fullPath}`);

  const existing = findNodeByPath(fullPath);
  if (existing) {
    await filesystemActions.openFile(existing);
    return;
  }

  const folderNode = findNodeByPath(settings.folder);
  if (!folderNode) {
    log.info(`Creating folder: ${settings.folder}`);
    await filesystemActions.createFolder(
      "/",
      settings.folder.replace(/^\//, ""),
    );
    await filesystemActions.loadTree();
  }

  const content = await getTemplateContent();
  const node = await filesystemActions.createFile(
    settings.folder,
    filename,
    content,
  );

  if (node) {
    await filesystemActions.openFile(node);
    showNotification(`Created daily note: ${dateStr}`, "success");
  }
}

export function getDailyNotesForMonth(
  year: number,
  month: number,
): Set<number> {
  const settings = getSettings();
  const nodes = get(rootNodes);
  const days = new Set<number>();

  function findFolder(nodes: FsNode[]): FsNode | null {
    for (const node of nodes) {
      if (node.path === settings.folder && node.type === "folder") {
        return node;
      }
      if (node.children) {
        const found = findFolder(node.children);
        if (found) return found;
      }
    }
    return null;
  }

  const folder = findFolder(nodes);
  if (!folder?.children) return days;

  for (const file of folder.children) {
    if (file.type !== "file") continue;
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
