# Plan: Move files/folders via drag-and-drop from context menu

## Tech Stack

- Language: TypeScript
- Framework: Svelte 5 (runes), SvelteKit
- Testing: Vitest + existing snapshot tests

## Structure

Changes to existing files only:

```
frontend/src/lib/
├── stores/
│   └── filesystem.ts        # add moveNode action + movingNode store
├── components/
│   ├── FileTree.svelte       # add "Move" menu item, drop zone on tree root
│   └── FileTreeItem.svelte   # drag source + drop target behavior
```

## Approach

### 1. Add `movingNode` store and `moveNode` action

In `filesystem.ts`:
- New store: `movingNode = writable<FsNode | null>(null)` — tracks the node being moved.
- New action: `moveNode(node, newParentPath)` — calls `api.moveNode(id, { new_parent_path })`, reloads tree, updates `currentFile` if affected.

### 2. Add "Move" context menu item

In `FileTree.svelte`:
- Add `{ label: 'Move', action: handleMoveClick }` to `menuItems` (only when a node is selected).
- `handleMoveClick()` sets `movingNode` store to the selected node.
- This makes the node draggable and visually highlights it.

### 3. Make the moving node draggable

In `FileTreeItem.svelte`:
- When `movingNode` matches this node, set `draggable="true"` on the item-row button.
- Handle `ondragstart`: set `dataTransfer` with the node's ID and path.
- Visual: add a `.moving` CSS class (subtle outline or opacity change) so the user sees which node is in move mode.

### 4. Make folders (and tree root) accept drops

In `FileTreeItem.svelte` (for folders):
- Handle `ondragover`: prevent default to allow drop. Add `.drop-target` CSS class for visual feedback (highlight border/background).
- Handle `ondragleave`: remove `.drop-target` class.
- Handle `ondrop`: read node ID from `dataTransfer`, call `filesystemActions.moveNode(node, folder.path)`, clear `movingNode`.
- Validation: don't allow dropping onto self, onto own children, or onto current parent (no-op).

In `FileTree.svelte` (for root level):
- Same drop handlers on the `.file-tree` container to allow moving items to root (`/`).

### 5. Cancel move mode

- Pressing `Escape` clears `movingNode` (listen in FileTree).
- Clicking anywhere without dropping clears `movingNode`.
- Successful drop clears `movingNode`.

### 6. CSS feedback states

- `.moving`: the node being moved — subtle dashed border or reduced opacity.
- `.drop-target`: valid folder hover — accent-colored border or background highlight.
- Invalid targets (self, children of moving node) get no drop-target styling (cursor stays default).

## Risks

- **Dropping onto own descendant**: Would create circular path. Mitigation: walk up from drop target to check if moving node is an ancestor. Backend also returns 409 on conflict.
- **Mobile support**: HTML drag-and-drop doesn't work on touch devices. Mitigation: for now, keep the existing long-press context menu; mobile move can use a "Move to..." folder picker modal in a future iteration. The "Move" menu item can still appear — it just enables desktop drag; on mobile we can skip drag and show a simple target picker later.
- **Currently open file gets moved**: Its path changes. Mitigation: after move, if `currentFile.id` matches moved node, update `currentFile` with the new path from the API response.

## Open Questions

- Should "Move" also work without drag (e.g., click "Move", then click a destination folder)? This would be simpler for keyboard/mobile users. **Recommendation**: start with drag-only; add click-to-place as a follow-up if needed.
