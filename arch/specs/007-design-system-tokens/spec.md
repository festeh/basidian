# Spec: Design System Tokens

## Problem

Colors are well-systematized (17 CSS variables, 5 themes, type-safe switching). Everything else is hardcoded: spacing, border-radius, font sizes, shadows, z-index, and transitions use magic numbers scattered across 29 components. Changing the visual rhythm or density of the app means hunting through every file.

## Goal

Extend the existing CSS variable pattern to cover non-color tokens. Make it possible to change the app's spatial feel by editing one file.

## What to tokenize

### Spacing scale
Semantic names on a 4px-based scale covering all current values:
- `hairline` (2px), `tight` (4px), `snug` (6px), `compact` (8px), `cozy` (12px), `comfortable` (16px), `spacious` (20px), `loose` (24px), `wide` (32px)

### Border-radius scale
Four sizes covering all current usage:
- `subtle` (4px), `default` (6px), `rounded` (8px), `prominent` (12px)
- `50%` stays as a literal — it's a shape (circle), not a design token.

### Font-size scale
Named sizes for the 7 distinct pixel values in use:
- `caption` (10px), `label` (12px), `detail` (13px), `body` (14px), `subheading` (16px), `heading` (18px), `title` (20px)

### Shadow scale
Named shadows for the 3 patterns in use:
- `subtle` — light popover shadow
- `raised` — panel/dropdown shadow
- `floating` — heavy dialog shadow
- `sidebar` / `topbar` — keep existing directional shadows

### Z-index scale
Named layers instead of magic numbers:
- `raised` (1), `sticky` (10), `overlay` (100), `modal` (1000)

### Backdrop color
One variable instead of three repeated `rgba(0,0,0,0.5)`:
- `--color-backdrop`

## What NOT to tokenize

- **MarkdownPreview `em` units** — these are intentionally relative to rendered content, not the UI. Leave them alone.
- **Transition durations** — only a few exist and they're all similar. Not worth a token until there are more.
- **Component-specific layout values** (sidebar width) — these are structural, not design tokens. Keep them where they are.

## Constraints

- All tokens go in `app.css` alongside existing color variables.
- No new files, build tools, or preprocessors.
- No changes to the theme switching system — these tokens are theme-independent.
- Components should use the tokens but the visual result should be identical (pixel-perfect, no visual changes).
