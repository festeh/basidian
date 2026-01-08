<script lang="ts">
	import MarkdownIt, { type Options } from 'markdown-it';
	import type Token from 'markdown-it/lib/token.mjs';
	import type Renderer from 'markdown-it/lib/renderer.mjs';
	import { codeToHtml } from 'shiki';
	import katex from 'katex';
	import { currentTheme } from '$lib/stores/theme';

	interface Props {
		content: string;
	}

	let { content }: Props = $props();
	let shikiTheme = $derived($currentTheme.shikiTheme);

	let renderedHtml = $state('');

	const md = new MarkdownIt({
		html: true,
		linkify: true,
		typographer: true
	});

	// Custom fence renderer for code blocks (will be replaced with shiki)
	md.renderer.rules.fence = (
		tokens: Token[],
		idx: number,
		_options: Options,
		_env: unknown,
		_self: Renderer
	): string => {
		const token = tokens[idx];
		const lang = token.info.trim() || 'text';
		const code = token.content;

		// Return placeholder that we'll replace with shiki output
		return `<pre class="shiki-placeholder" data-lang="${lang}" data-code="${encodeURIComponent(code)}"></pre>`;
	};

	// LaTeX rendering helper
	function renderLatex(text: string): string {
		// Block math: $$...$$
		text = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
			try {
				return `<div class="math-block">${katex.renderToString(math.trim(), { displayMode: true, throwOnError: false })}</div>`;
			} catch {
				return `<div class="math-error">LaTeX error: ${math}</div>`;
			}
		});

		// Inline math: $...$
		text = text.replace(/\$([^\$\n]+?)\$/g, (_, math) => {
			try {
				return katex.renderToString(math.trim(), { displayMode: false, throwOnError: false });
			} catch {
				return `<span class="math-error">LaTeX error: ${math}</span>`;
			}
		});

		return text;
	}

	async function renderMarkdown(source: string) {
		// First render LaTeX in source
		const withLatex = renderLatex(source);

		// Then render markdown
		let html = md.render(withLatex);

		// Find all shiki placeholders and replace with highlighted code
		const placeholderRegex =
			/<pre class="shiki-placeholder" data-lang="([^"]*)" data-code="([^"]*)"><\/pre>/g;
		const matches = [...html.matchAll(placeholderRegex)];

		for (const match of matches) {
			const [placeholder, lang, encodedCode] = match;
			const code = decodeURIComponent(encodedCode);

			try {
				const highlighted = await codeToHtml(code, {
					lang: lang || 'text',
					theme: shikiTheme as any
				});
				html = html.replace(placeholder, highlighted);
			} catch {
				// Fallback if language not supported
				const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
				html = html.replace(placeholder, `<pre class="code-block"><code>${escaped}</code></pre>`);
			}
		}

		return html;
	}

	$effect(() => {
		// Re-render when content or theme changes
		const _ = shikiTheme;
		renderMarkdown(content).then((html) => {
			renderedHtml = html;
		});
	});
</script>

<div class="markdown-preview">
	{@html renderedHtml}
</div>

<style>
	.markdown-preview {
		padding: 16px 24px;
		overflow-y: auto;
		height: 100%;
		line-height: 1.7;
	}

	/* Headers */
	.markdown-preview :global(h1) {
		font-size: 2em;
		font-weight: 700;
		margin: 1em 0 0.5em;
		padding-bottom: 0.3em;
		border-bottom: 1px solid var(--color-overlay);
	}

	.markdown-preview :global(h2) {
		font-size: 1.5em;
		font-weight: 600;
		margin: 1em 0 0.5em;
		padding-bottom: 0.3em;
		border-bottom: 1px solid var(--color-overlay);
	}

	.markdown-preview :global(h3) {
		font-size: 1.25em;
		font-weight: 600;
		margin: 1em 0 0.5em;
	}

	.markdown-preview :global(h4),
	.markdown-preview :global(h5),
	.markdown-preview :global(h6) {
		font-size: 1em;
		font-weight: 600;
		margin: 1em 0 0.5em;
	}

	/* Paragraphs */
	.markdown-preview :global(p) {
		margin: 0.8em 0;
	}

	/* Links */
	.markdown-preview :global(a) {
		color: var(--color-accent);
		text-decoration: none;
	}

	.markdown-preview :global(a:hover) {
		text-decoration: underline;
	}

	/* Inline code */
	.markdown-preview :global(code:not(pre code)) {
		background-color: var(--color-surface);
		padding: 0.2em 0.4em;
		border-radius: 4px;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		font-size: 0.9em;
	}

	/* Code blocks (shiki) */
	.markdown-preview :global(pre) {
		margin: 1em 0;
		padding: 16px;
		border-radius: 8px;
		overflow-x: auto;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		font-size: 14px;
		line-height: 1.5;
	}

	.markdown-preview :global(pre.shiki) {
		background-color: var(--color-mantle) !important;
	}

	.markdown-preview :global(.code-block) {
		background-color: var(--color-mantle);
	}

	/* Blockquotes */
	.markdown-preview :global(blockquote) {
		margin: 1em 0;
		padding: 0.5em 1em;
		border-left: 4px solid var(--color-accent);
		background-color: var(--color-surface);
		color: var(--color-subtext);
	}

	.markdown-preview :global(blockquote p) {
		margin: 0.5em 0;
	}

	/* Lists */
	.markdown-preview :global(ul),
	.markdown-preview :global(ol) {
		margin: 0.8em 0;
		padding-left: 2em;
	}

	.markdown-preview :global(li) {
		margin: 0.3em 0;
	}

	/* Task lists */
	.markdown-preview :global(li input[type='checkbox']) {
		margin-right: 0.5em;
	}

	/* Tables */
	.markdown-preview :global(table) {
		width: 100%;
		margin: 1em 0;
		border-collapse: collapse;
	}

	.markdown-preview :global(th),
	.markdown-preview :global(td) {
		padding: 0.5em 1em;
		border: 1px solid var(--color-overlay);
	}

	.markdown-preview :global(th) {
		background-color: var(--color-surface);
		font-weight: 600;
	}

	.markdown-preview :global(tr:nth-child(even)) {
		background-color: var(--color-surface);
	}

	/* Horizontal rules */
	.markdown-preview :global(hr) {
		margin: 2em 0;
		border: none;
		border-top: 1px solid var(--color-overlay);
	}

	/* Images */
	.markdown-preview :global(img) {
		max-width: 100%;
		height: auto;
		border-radius: 8px;
	}

	/* Math */
	.markdown-preview :global(.math-block) {
		margin: 1em 0;
		overflow-x: auto;
		text-align: center;
	}

	.markdown-preview :global(.math-error) {
		color: var(--color-error);
		font-family: monospace;
	}

	/* Bold and italic */
	.markdown-preview :global(strong) {
		font-weight: 700;
	}

	.markdown-preview :global(em) {
		font-style: italic;
	}

	/* Strikethrough */
	.markdown-preview :global(del) {
		text-decoration: line-through;
		color: var(--color-subtext);
	}
</style>
