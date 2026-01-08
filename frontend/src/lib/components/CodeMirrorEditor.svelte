<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view';
	import { EditorState } from '@codemirror/state';
	import { markdown, markdownLanguage } from '@codemirror/lang-markdown';
	import { languages } from '@codemirror/language-data';
	import {
		defaultKeymap,
		history,
		historyKeymap,
		indentWithTab
	} from '@codemirror/commands';
	import {
		syntaxHighlighting,
		defaultHighlightStyle,
		bracketMatching,
		indentOnInput
	} from '@codemirror/language';

	interface Props {
		content: string;
		onchange: (content: string) => void;
	}

	let { content, onchange }: Props = $props();

	let editorContainer: HTMLDivElement;
	let view: EditorView | null = null;

	// Theme based on CSS variables
	const theme = EditorView.theme({
		'&': {
			height: '100%',
			fontSize: '14px'
		},
		'.cm-content': {
			fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
			padding: '16px 0'
		},
		'.cm-line': {
			padding: '0 16px'
		},
		'.cm-gutters': {
			backgroundColor: 'var(--color-mantle)',
			color: 'var(--color-subtext)',
			border: 'none',
			paddingRight: '8px'
		},
		'.cm-activeLineGutter': {
			backgroundColor: 'var(--color-surface)'
		},
		'.cm-activeLine': {
			backgroundColor: 'var(--color-surface)'
		},
		'.cm-cursor': {
			borderLeftColor: 'var(--color-text)'
		},
		'.cm-selectionBackground': {
			backgroundColor: 'var(--color-overlay) !important'
		},
		'&.cm-focused .cm-selectionBackground': {
			backgroundColor: 'var(--color-overlay) !important'
		},
		'.cm-scroller': {
			overflow: 'auto'
		}
	});

	// Base theme for light/dark modes
	const baseTheme = EditorView.baseTheme({
		'&.cm-editor': {
			backgroundColor: 'var(--color-base)'
		},
		'.cm-content': {
			caretColor: 'var(--color-text)'
		}
	});

	onMount(() => {
		const startState = EditorState.create({
			doc: content,
			extensions: [
				lineNumbers(),
				highlightActiveLine(),
				history(),
				bracketMatching(),
				indentOnInput(),
				markdown({
					base: markdownLanguage,
					codeLanguages: languages
				}),
				syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
				keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
				theme,
				baseTheme,
				EditorView.updateListener.of((update) => {
					if (update.docChanged) {
						const newContent = update.state.doc.toString();
						onchange(newContent);
					}
				}),
				EditorView.lineWrapping
			]
		});

		view = new EditorView({
			state: startState,
			parent: editorContainer
		});
	});

	onDestroy(() => {
		if (view) {
			view.destroy();
		}
	});

	// Update editor content when prop changes externally
	$effect(() => {
		if (view && content !== view.state.doc.toString()) {
			view.dispatch({
				changes: {
					from: 0,
					to: view.state.doc.length,
					insert: content
				}
			});
		}
	});
</script>

<div class="codemirror-container" bind:this={editorContainer}></div>

<style>
	.codemirror-container {
		height: 100%;
		overflow: hidden;
	}

	.codemirror-container :global(.cm-editor) {
		height: 100%;
	}
</style>
