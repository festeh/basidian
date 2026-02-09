<script lang="ts">
	interface Props {
		content?: string;
		onchange?: (value: string) => void;
	}

	let { content = '', onchange }: Props = $props();
</script>

<div data-testid="codemirror-mock">{content}</div>
