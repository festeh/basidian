import type {
	SyncChangesResponse,
	SyncNodeRow,
	SyncContentRow,
	SyncPushResponse
} from './types';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8090/api';

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const text = await response.text();
		throw new Error(`HTTP ${response.status}: ${text}`);
	}
	return response.json();
}

export async function fetchChanges(since?: string): Promise<SyncChangesResponse> {
	const url = since
		? `${BASE_URL}/sync/changes?since=${encodeURIComponent(since)}`
		: `${BASE_URL}/sync/changes`;
	const response = await fetch(url);
	return handleResponse<SyncChangesResponse>(response);
}

export async function pushChanges(
	nodes: SyncNodeRow[],
	content: SyncContentRow[]
): Promise<SyncPushResponse> {
	const response = await fetch(`${BASE_URL}/sync/push`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ nodes, content })
	});
	return handleResponse<SyncPushResponse>(response);
}
