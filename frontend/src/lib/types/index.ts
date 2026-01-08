export type FsNodeType = 'folder' | 'file';

export interface FsNode {
	id?: string;
	type: FsNodeType;
	name: string;
	path: string;
	parent_path: string;
	content?: string;
	sort_order: number;
	created_at?: string;
	updated_at?: string;
	// Client-side UI state
	children?: FsNode[];
	isExpanded?: boolean;
	isLoading?: boolean;
}

export interface CreateNodeRequest {
	type: FsNodeType;
	name: string;
	parent_path: string;
	content?: string;
	sort_order?: number;
}

export interface MoveNodeRequest {
	new_parent_path?: string;
	new_name?: string;
}

export interface Theme {
	name: string;
	displayName: string;
	isDark: boolean;
	shikiTheme: string;
	colors: {
		base: string;
		mantle: string;
		surface: string;
		overlay: string;
		text: string;
		subtext: string;
		accent: string;
		secondary: string;
		error: string;
		success: string;
		// Code syntax highlighting colors
		codeKeyword: string;
		codeString: string;
		codeComment: string;
		codeNumber: string;
		codeFunction: string;
		codeVariable: string;
		codeOperator: string;
	};
}

export type ThemeName =
	| 'catppuccin-mocha'
	| 'catppuccin-latte'
	| 'nord'
	| 'dracula'
	| 'gruvbox-dark';

export interface Settings {
	vimMode: boolean;
}
