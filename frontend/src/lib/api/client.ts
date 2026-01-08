import type { FsNode, CreateNodeRequest, MoveNodeRequest } from '$lib/types';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8090/api';

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const error = await response.text();
		throw new Error(`HTTP ${response.status}: ${error}`);
	}
	return response.json();
}

export const api = {
	// Get file tree
	async getTree(parentPath?: string): Promise<FsNode[]> {
		const url = parentPath
			? `${BASE_URL}/fs/tree?parent_path=${encodeURIComponent(parentPath)}`
			: `${BASE_URL}/fs/tree`;
		const response = await fetch(url);
		return handleResponse<FsNode[]>(response);
	},

	// Get single node by ID
	async getNode(id: string): Promise<FsNode> {
		const response = await fetch(`${BASE_URL}/fs/node/${id}`);
		return handleResponse<FsNode>(response);
	},

	// Get single node by path
	async getNodeByPath(path: string): Promise<FsNode> {
		const response = await fetch(`${BASE_URL}/fs/node?path=${encodeURIComponent(path)}`);
		return handleResponse<FsNode>(response);
	},

	// Create new node
	async createNode(node: CreateNodeRequest): Promise<FsNode> {
		const response = await fetch(`${BASE_URL}/fs/node`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(node)
		});
		return handleResponse<FsNode>(response);
	},

	// Update node
	async updateNode(node: FsNode): Promise<FsNode> {
		const response = await fetch(`${BASE_URL}/fs/node/${node.id}`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(node)
		});
		return handleResponse<FsNode>(response);
	},

	// Delete node
	async deleteNode(id: string): Promise<void> {
		const response = await fetch(`${BASE_URL}/fs/node/${id}`, {
			method: 'DELETE'
		});
		if (!response.ok) {
			throw new Error(`Failed to delete node: ${response.status}`);
		}
	},

	// Move or rename node
	async moveNode(id: string, request: MoveNodeRequest): Promise<FsNode> {
		const response = await fetch(`${BASE_URL}/fs/move/${id}`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(request)
		});
		return handleResponse<FsNode>(response);
	},

	// Search files
	async searchFiles(query: string): Promise<FsNode[]> {
		const response = await fetch(`${BASE_URL}/fs/search?q=${encodeURIComponent(query)}`);
		return handleResponse<FsNode[]>(response);
	}
};
