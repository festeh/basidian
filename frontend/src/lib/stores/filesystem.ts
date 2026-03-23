import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';
import type { FsNode } from '$lib/types';
import * as dbNodes from '$lib/db/nodes';
import { schedulePush } from '$lib/sync/engine';
import { createLogger } from '$lib/utils/logger';
const log = createLogger('Filesystem');

const EXPANDED_PATHS_KEY = 'basidian-expanded-paths';

// State stores
export const rootNodes = writable<FsNode[]>([]);
export const selectedNode = writable<FsNode | null>(null);
export const currentFile = writable<FsNode | null>(null);
export const expandedPaths = writable<Set<string>>(new Set());
export const renamingPath = writable<string | null>(null);
export const movingNode = writable<FsNode | null>(null);
export const isLoading = writable(false);
export const isLoadingFile = writable(false);
export const error = writable<string | null>(null);

function loadExpandedPaths(): Set<string> {
	if (browser) {
		try {
			const stored = localStorage.getItem(EXPANDED_PATHS_KEY);
			if (stored) {
				return new Set(JSON.parse(stored));
			}
		} catch {
			// Ignore parse errors
		}
	}
	return new Set();
}

function saveExpandedPaths(paths: Set<string>) {
	if (browser) {
		localStorage.setItem(EXPANDED_PATHS_KEY, JSON.stringify([...paths]));
	}
}

// Initialize expanded paths
if (browser) {
	expandedPaths.set(loadExpandedPaths());
}

function buildTree(flatNodes: FsNode[]): FsNode[] {
	const nodeMap = new Map<string, FsNode>();
	const roots: FsNode[] = [];
	const expanded = get(expandedPaths);

	// Create map by ID with initialized children
	for (const node of flatNodes) {
		if (node.id) {
			nodeMap.set(node.id, {
				...node,
				children: [],
				isExpanded: expanded.has(node.path)
			});
		}
	}

	// Build hierarchy using parent_id
	for (const node of flatNodes) {
		const treeNode = nodeMap.get(node.id!)!;
		if (!node.parent_id) {
			roots.push(treeNode);
		} else {
			const parent = nodeMap.get(node.parent_id);
			if (parent) {
				parent.children!.push(treeNode);
			} else {
				roots.push(treeNode);
			}
		}
	}

	// Sort: folders first, then by sort_order, then by name
	function sortNodes(nodes: FsNode[]) {
		nodes.sort((a, b) => {
			if (a.type === 'folder' && b.type === 'file') return -1;
			if (a.type === 'file' && b.type === 'folder') return 1;
			if (a.sort_order !== b.sort_order) return a.sort_order - b.sort_order;
			return a.name.localeCompare(b.name);
		});
		for (const node of nodes) {
			if (node.children?.length) sortNodes(node.children);
		}
	}

	sortNodes(roots);
	return roots;
}

export const filesystemActions = {
	async loadTree() {
		isLoading.set(true);
		error.set(null);
		try {
			const nodes = await dbNodes.getTree();
			rootNodes.set(buildTree(nodes));
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Failed to load tree');
		} finally {
			isLoading.set(false);
		}
	},

	toggleFolder(node: FsNode) {
		if (node.type !== 'folder') return;

		const paths = get(expandedPaths);
		const wasExpanded = node.isExpanded;

		if (wasExpanded) {
			paths.delete(node.path);
		} else {
			paths.add(node.path);
		}

		expandedPaths.set(paths);
		saveExpandedPaths(paths);

		// Update node in tree
		rootNodes.update((nodes) => {
			function updateNode(list: FsNode[]): FsNode[] {
				return list.map((n) => {
					if (n.path === node.path) {
						return { ...n, isExpanded: !wasExpanded };
					}
					if (n.children?.length) {
						return { ...n, children: updateNode(n.children) };
					}
					return n;
				});
			}
			return updateNode(nodes);
		});
	},

	selectNode(node: FsNode | null) {
		selectedNode.set(node);
	},

	async openFile(node: FsNode) {
		if (node.type !== 'file') return;

		isLoadingFile.set(true);
		error.set(null);
		try {
			const fullNode = node.id ? await dbNodes.getNode(node.id) : node;
			currentFile.set(fullNode);
			selectedNode.set(fullNode);
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Failed to load file');
		} finally {
			isLoadingFile.set(false);
		}
	},

	closeFile() {
		currentFile.set(null);
	},

	async createFile(parentPath: string, name: string, content = '') {
		try {
			const node = await dbNodes.createNode('file', name, parentPath, content);
			await this.loadTree();
			schedulePush();
			return node;
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Failed to create file');
			return null;
		}
	},

	async createFolder(parentPath: string, name: string) {
		try {
			const node = await dbNodes.createNode('folder', name, parentPath);
			await this.loadTree();
			schedulePush();
			return node;
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Failed to create folder');
			return null;
		}
	},

	async updateNode(node: FsNode) {
		try {
			const updated = await dbNodes.updateNode(node.id!, {
				name: node.name,
				content: node.content ?? undefined,
				sort_order: node.sort_order
			});
			if (!updated) return null;
			const current = get(currentFile);
			if (current?.id === node.id) {
				currentFile.set(updated);
			}
			// Update in tree
			rootNodes.update((nodes) => {
				function updateInTree(list: FsNode[]): FsNode[] {
					return list.map((n) => {
						if (n.id === updated!.id) {
							return { ...updated!, children: n.children, isExpanded: n.isExpanded };
						}
						if (n.children?.length) {
							return { ...n, children: updateInTree(n.children) };
						}
						return n;
					});
				}
				return updateInTree(nodes);
			});
			schedulePush();
			return updated;
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Failed to update node');
			return null;
		}
	},

	async deleteNode(node: FsNode) {
		try {
			await dbNodes.softDeleteNode(node.id!);
			const current = get(currentFile);
			if (current?.id === node.id) {
				currentFile.set(null);
			}
			const selected = get(selectedNode);
			if (selected?.id === node.id) {
				selectedNode.set(null);
			}
			await this.loadTree();
			schedulePush();
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Failed to delete node');
		}
	},

	async moveNode(node: FsNode, newParentPath: string) {
		log.info('moveNode', { id: node.id, from: node.parent_path, to: newParentPath });
		try {
			const updated = await dbNodes.moveNode(node.id!, newParentPath);
			log.debug('move success', { updated });
			movingNode.set(null);
			await this.loadTree();
			schedulePush();

			const current = get(currentFile);
			if (current && current.id === node.id && updated) {
				currentFile.set({ ...updated, content: current.content });
			}
		} catch (e) {
			log.error('move failed', e);
			movingNode.set(null);
			error.set(e instanceof Error ? e.message : 'Failed to move node');
		}
	},

	async renameNode(node: FsNode, newName: string) {
		log.info('renameNode', { id: node.id, from: node.name, to: newName });
		try {
			const updated = await dbNodes.moveNode(node.id!, undefined, newName);
			log.debug('rename success', { updated });
			await this.loadTree();
			schedulePush();

			const current = get(currentFile);
			if (current && current.id === node.id && updated) {
				currentFile.set({ ...updated, content: current.content });
			}
		} catch (e) {
			log.error('rename failed', e);
			error.set(e instanceof Error ? e.message : 'Failed to rename node');
		}
	},

	async searchFiles(query: string): Promise<FsNode[]> {
		try {
			return await dbNodes.searchFiles(query);
		} catch (e) {
			error.set(e instanceof Error ? e.message : 'Search failed');
			return [];
		}
	},

	clearError() {
		error.set(null);
	}
};
