export interface SyncNodeRow {
	id: string;
	parent_id: string | null;
	type: string;
	name: string;
	path: string;
	sort_order: number;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
}

export interface SyncContentRow {
	node_id: string;
	body: string;
	updated_at: string;
}

export interface SyncChangesResponse {
	nodes: SyncNodeRow[];
	content: SyncContentRow[];
	server_time: string;
}

export interface SyncPushResult {
	id: string;
	accepted: boolean;
	reason?: string;
	server_updated_at?: string;
}

export interface SyncPushResponse {
	results: SyncPushResult[];
	server_time: string;
}
