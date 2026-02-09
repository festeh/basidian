<script lang="ts">
	interface Props {
		content?: string;
	}

	let { content = '' }: Props = $props();
</script>

<div data-testid="markdown-preview-mock">{content}</div>
