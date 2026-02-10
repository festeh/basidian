<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view';
	import { EditorState, type Extension, Annotation } from '@codemirror/state';
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
	import { vim } from '@replit/codemirror-vim';
	import { settings } from '$lib/stores/settings';

	interface Props {
		content: string;
		onchange: (content: string) => void;
	}

	let { content, onchange }: Props = $props();

	let editorContainer: HTMLDivElement;
	let view: EditorView | null = null;
	let previousVimMode: boolean | null = null;

	// Annotation to mark programmatic content updates
	const externalUpdate = Annotation.define<boolean>();

	// Theme based on CSS variables
	const theme = EditorView.theme({
		'&': {
			height: '100%',
			fontSize: 'var(--font-size-base)'
		},
		'.cm-content': {
			fontFamily: 'var(--font-mono)',
			padding: 'var(--space-comfortable) 0'
		},
		'.cm-line': {
			padding: '0 var(--space-comfortable)'
		},
		'.cm-gutters': {
			backgroundColor: 'var(--color-mantle)',
			color: 'var(--color-subtext)',
			border: 'none',
			paddingRight: 'var(--space-compact)'
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

	function createEditor(useVim: boolean) {
		const extensions: Extension[] = [
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
					const isExternal = update.transactions.some((tr) => tr.annotation(externalUpdate));
					if (!isExternal) {
						onchange(update.state.doc.toString());
					}
				}
			}),
			EditorView.lineWrapping
		];

		if (useVim) {
			extensions.unshift(vim());
		}

		const startState = EditorState.create({
			doc: content,
			extensions
		});

		return new EditorView({
			state: startState,
			parent: editorContainer
		});
	}

	onMount(() => {
		previousVimMode = $settings.vimMode;
		view = createEditor(previousVimMode);
	});

	onDestroy(() => {
		if (view) {
			view.destroy();
		}
	});

	// Recreate editor only when vim mode actually changes
	$effect(() => {
		const newVimMode = $settings.vimMode;
		if (previousVimMode !== null && previousVimMode !== newVimMode) {
			const currentContent = view?.state.doc.toString() ?? content;
			if (view) {
				view.destroy();
			}
			view = createEditor(newVimMode);
			if (currentContent !== content) {
				view.dispatch({
					changes: {
						from: 0,
						to: view.state.doc.length,
						insert: currentContent
					},
					annotations: externalUpdate.of(true)
				});
			}
		}
		previousVimMode = newVimMode;
	});

	// Update editor content when prop changes externally
	$effect(() => {
		if (view && content !== view.state.doc.toString()) {
			view.dispatch({
				changes: {
					from: 0,
					to: view.state.doc.length,
					insert: content
				},
				annotations: externalUpdate.of(true)
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
