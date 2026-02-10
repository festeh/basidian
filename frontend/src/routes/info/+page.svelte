<script lang="ts">
	import { goto } from '$app/navigation';

	const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8090/api';
	const buildTimestamp = __BUILD_TIMESTAMP__;

	function goBack() {
		goto('/');
	}

	function formatDate(isoString: string): string {
		const date = new Date(isoString);
		return date.toLocaleString();
	}
</script>

<div class="info">
	<header>
		<button class="back-btn" onclick={goBack} aria-label="Go back">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
			</svg>
		</button>
		<h1>Info</h1>
	</header>

	<main>
		<section>
			<h2>Application</h2>
			<div class="info-list">
				<div class="info-row">
					<span class="info-label">Name</span>
					<span class="info-value">Basidian</span>
				</div>
				<div class="info-row">
					<span class="info-label">Version</span>
					<span class="info-value">0.1.0</span>
				</div>
				<div class="info-row">
					<span class="info-label">Build Time</span>
					<span class="info-value">{formatDate(buildTimestamp)}</span>
				</div>
			</div>
		</section>

		<section>
			<h2>Backend</h2>
			<div class="info-list">
				<div class="info-row">
					<span class="info-label">API URL</span>
					<span class="info-value monospace">{backendUrl}</span>
				</div>
			</div>
		</section>
	</main>
</div>

<style>
	.info {
		height: 100vh;
		overflow-y: auto;
		background-color: var(--color-base);
		padding-left: var(--safe-area-inset-left);
		padding-right: var(--safe-area-inset-right);
		padding-bottom: var(--safe-area-inset-bottom);
	}

	header {
		display: flex;
		align-items: center;
		gap: var(--space-cozy);
		padding: var(--space-comfortable);
		padding-top: calc(var(--space-comfortable) + var(--safe-area-inset-top));
		background-color: var(--color-surface);
		border-bottom: 1px solid var(--color-overlay);
	}

	header h1 {
		font-size: var(--text-title);
		font-weight: 600;
	}

	.back-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border: none;
		background: transparent;
		color: var(--color-text);
		border-radius: var(--radius-rounded);
		cursor: pointer;
	}

	.back-btn:hover {
		background-color: var(--color-overlay);
	}

	main {
		padding: var(--space-loose);
		max-width: 600px;
	}

	section + section {
		margin-top: var(--space-loose);
	}

	section h2 {
		font-size: var(--text-subheading);
		color: var(--color-accent);
		margin-bottom: var(--space-comfortable);
	}

	.info-list {
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-prominent);
		overflow: hidden;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--space-comfortable);
	}

	.info-row + .info-row {
		border-top: 1px solid var(--color-overlay);
	}

	.info-label {
		color: var(--color-subtext);
		font-size: var(--text-body);
	}

	.info-value {
		color: var(--color-text);
		font-size: var(--text-body);
		font-weight: 500;
	}

	.info-value.monospace {
		font-family: monospace;
		font-size: var(--text-detail);
	}
</style>
