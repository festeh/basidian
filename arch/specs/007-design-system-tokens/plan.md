# Plan: Design System Tokens

**Spec**: arch/specs/007-design-system-tokens/spec.md

## Tech Stack

- Language: CSS + Svelte 5 (scoped styles)
- Framework: SvelteKit (no new dependencies)
- Testing: Playwright visual regression (existing snapshots catch regressions)

## Structure

Only one file gets new content. All other changes are replacements inside existing files.

```
frontend/src/
├── app.css                          # ADD token variables to :root
├── lib/components/
│   ├── Backdrop.svelte              # Replace hardcoded values
│   ├── CodeMirrorEditor.svelte      # Replace hardcoded values
│   ├── ConfirmDialog.svelte         # Replace hardcoded values
│   ├── ContextMenu.svelte           # Replace hardcoded values
│   ├── Editor.svelte                # Replace hardcoded values
│   ├── FileTree.svelte              # Replace hardcoded values
│   ├── FileTreeItem.svelte          # Replace hardcoded values
│   ├── MarkdownPreview.svelte       # Replace ONLY non-em values
│   ├── Modal.svelte                 # Replace hardcoded values
│   ├── Sidebar.svelte               # Replace hardcoded values
│   ├── StatusBar.svelte             # Replace hardcoded values
│   ├── TopBar.svelte                # Replace hardcoded values
│   ├── TopBarDesktop.svelte         # Replace hardcoded values
│   └── TopBarMobile.svelte          # Replace hardcoded values
├── lib/plugins/
│   ├── PluginSlot.svelte            # Replace hardcoded values
│   └── installed/
│       ├── ai-chat/*.svelte         # Replace hardcoded values
│       └── daily-notes/*.svelte     # Replace hardcoded values
├── routes/
│   ├── +page.svelte                 # Replace hardcoded values
│   ├── PageDesktop.svelte           # Replace hardcoded values
│   ├── PageMobile.svelte            # Replace hardcoded values
│   ├── info/+page.svelte            # Replace hardcoded values
│   └── settings/+page.svelte        # Replace hardcoded values
```

## Approach

### Step 1: Define tokens in app.css

Add new variable blocks to the existing `:root` section, after the color and typography variables. Group by category with comments.

```css
/* Spacing */
--space-hairline: 2px;
--space-tight: 4px;
--space-snug: 6px;
--space-compact: 8px;
--space-cozy: 12px;
--space-comfortable: 16px;
--space-spacious: 20px;
--space-loose: 24px;
--space-wide: 32px;

/* Border radius */
--radius-subtle: 4px;
--radius-default: 6px;
--radius-rounded: 8px;
--radius-prominent: 12px;

/* Font sizes */
--text-caption: 10px;
--text-label: 12px;
--text-detail: 13px;
--text-body: 14px;
--text-subheading: 16px;
--text-heading: 18px;
--text-title: 20px;

/* Shadows */
--shadow-subtle: 0 4px 12px rgba(0, 0, 0, 0.2);
--shadow-raised: 0 4px 12px rgba(0, 0, 0, 0.3);
--shadow-floating: 0 8px 32px rgba(0, 0, 0, 0.4);

/* Z-index layers */
--z-raised: 1;
--z-sticky: 10;
--z-overlay: 100;
--z-modal: 1000;

/* Backdrop */
--color-backdrop: rgba(0, 0, 0, 0.5);
```

### Step 2: Migrate components — core layout first

Start with high-traffic components that set the visual foundation:

1. **Editor.svelte** — padding, gaps, font sizes, radii, z-index
2. **Sidebar.svelte** — padding, gap, shadows
3. **PageDesktop.svelte** / **PageMobile.svelte** — z-index, radii

### Step 3: Migrate overlays and modals

These share the backdrop pattern and similar shadow/z-index values:

4. **Backdrop.svelte** — backdrop color
5. **Modal.svelte** — backdrop, shadow, radius, z-index, padding, font-size
6. **ConfirmDialog.svelte** — same as Modal
7. **ContextMenu.svelte** — shadow, radius, z-index, padding, font-size

### Step 4: Migrate secondary components

8. **StatusBar.svelte** — padding, gap, font-size, radius, shadow, z-index
9. **TopBar.svelte** / **TopBarDesktop.svelte** / **TopBarMobile.svelte** — padding, gap, z-index
10. **FileTree.svelte** / **FileTreeItem.svelte** — padding, gap, font-size, radius
11. **MarkdownPreview.svelte** — ONLY hardcoded px font-sizes and radii (skip em-based content styles)
12. **CodeMirrorEditor.svelte** — font-size

### Step 5: Migrate plugin components

13. **ChatPane.svelte** — padding, gap, font-size, radius, shadow, z-index
14. **ChatMessage.svelte** — padding, gap, font-size, radius
15. **ChatButton.svelte** — radius
16. **ai-chat/Settings.svelte** — padding, gap, font-size, radius
17. **daily-notes/DailyNoteButton.svelte** — padding, gap, font-size, radius, shadow, z-index
18. **daily-notes/Settings.svelte** — padding, gap, font-size

### Step 6: Migrate route pages

19. **+page.svelte** — padding, font-size, radius
20. **info/+page.svelte** — padding, gap, font-size, radius
21. **settings/+page.svelte** — padding, gap, font-size, radius

### Step 7: Run visual regression tests

Run the existing Playwright snapshot tests. They should pass with zero diff since all replacements are value-identical. If any pixel differences show up, fix the offending replacement.

## Risks

- **Pixel rounding**: CSS variables and direct values should produce identical results, but if any component uses `calc()` with tokens, sub-pixel differences could appear. Mitigation: visual regression tests catch this.
- **Forgetting a value**: Some hardcoded values may be missed. Mitigation: after migration, grep for remaining hardcoded px values in `<style>` blocks and verify each is intentional.
- **Over-tokenizing**: Not every `padding: 4px` needs a token — some are one-offs that won't benefit from centralization. Mitigation: use tokens only where the value matches the defined scale. If a component uses `10px` (not in the scale), leave it as-is rather than rounding.

## Naming Convention

Semantic names that describe the feel, not the size:

| Category | Names |
|----------|-------|
| Spacing | `hairline` · `tight` · `snug` · `compact` · `cozy` · `comfortable` · `spacious` · `loose` · `wide` |
| Radius | `subtle` · `default` · `rounded` · `prominent` |
| Text | `caption` · `label` · `detail` · `body` · `subheading` · `heading` · `title` |
| Shadow | `subtle` · `raised` · `floating` |
| Z-index | `raised` · `sticky` · `overlay` · `modal` |
