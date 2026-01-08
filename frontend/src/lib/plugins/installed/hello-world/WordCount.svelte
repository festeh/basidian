<script lang="ts">
	import { currentFile } from '$lib/stores/filesystem';

	const wordCount = $derived(
		($currentFile?.content || '').split(/\s+/).filter(Boolean).length
	);

	const charCount = $derived(($currentFile?.content || '').length);
</script>

{#if $currentFile}
	<div class="word-count">
		<span>{wordCount} words</span>
		<span class="separator">|</span>
		<span>{charCount} chars</span>
	</div>
{/if}

<style>
	.word-count {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 11px;
		color: var(--color-subtext);
	}

	.separator {
		opacity: 0.5;
	}
</style>
