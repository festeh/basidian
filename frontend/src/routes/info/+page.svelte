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
	}

	header {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 16px;
		background-color: var(--color-surface);
		border-bottom: 1px solid var(--color-overlay);
	}

	header h1 {
		font-size: 20px;
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
		border-radius: 8px;
		cursor: pointer;
	}

	.back-btn:hover {
		background-color: var(--color-overlay);
	}

	main {
		padding: 24px;
		max-width: 600px;
	}

	section + section {
		margin-top: 24px;
	}

	section h2 {
		font-size: 16px;
		color: var(--color-accent);
		margin-bottom: 16px;
	}

	.info-list {
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 12px;
		overflow: hidden;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 16px;
	}

	.info-row + .info-row {
		border-top: 1px solid var(--color-overlay);
	}

	.info-label {
		color: var(--color-subtext);
		font-size: 14px;
	}

	.info-value {
		color: var(--color-text);
		font-size: 14px;
		font-weight: 500;
	}

	.info-value.monospace {
		font-family: monospace;
		font-size: 13px;
	}
</style>
