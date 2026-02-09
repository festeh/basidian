/**
 * Flat node list as returned by the backend API.
 * The frontend's buildTree() handles nesting from parent_path.
 */
export const fakeTreeFlat = [
	{
		id: 'folder-projects',
		type: 'folder',
		name: 'Projects',
		path: '/Projects',
		parent_path: '/',
		sort_order: 0,
	},
	{
		id: 'file-meeting',
		type: 'file',
		name: 'Meeting Notes.md',
		path: '/Projects/Meeting Notes.md',
		parent_path: '/Projects',
		sort_order: 0,
	},
	{
		id: 'file-roadmap',
		type: 'file',
		name: 'Roadmap.md',
		path: '/Projects/Roadmap.md',
		parent_path: '/Projects',
		sort_order: 1,
	},
	{
		id: 'folder-daily',
		type: 'folder',
		name: 'Daily',
		path: '/Daily',
		parent_path: '/',
		sort_order: 1,
	},
	{
		id: 'file-today',
		type: 'file',
		name: '2026-02-08.md',
		path: '/Daily/2026-02-08.md',
		parent_path: '/Daily',
		sort_order: 0,
	},
	{
		id: 'file-welcome',
		type: 'file',
		name: 'Welcome.md',
		path: '/Welcome.md',
		parent_path: '/',
		sort_order: 2,
	},
];

export const fakeNote = {
	id: 'file-meeting',
	type: 'file',
	name: 'Meeting Notes.md',
	path: '/Projects/Meeting Notes.md',
	parent_path: '/Projects',
	sort_order: 0,
	content: [
		'# Meeting Notes',
		'',
		'## Agenda',
		'',
		'- Review Q1 progress',
		'- Discuss new plugin architecture',
		'- Plan next sprint',
		'',
		'## Action Items',
		'',
		'1. Update roadmap by Friday',
		'2. Create PR for search feature',
		'3. Schedule design review',
	].join('\n'),
};
