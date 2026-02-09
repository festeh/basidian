<script lang="ts">
	interface Props {
		onClose: () => void;
	}

	let { onClose }: Props = $props();
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="backdrop" onclick={onClose} onkeydown={() => {}}></div>

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		z-index: 99;
		animation: backdrop-fade 0.2s ease;
	}

	@keyframes backdrop-fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
