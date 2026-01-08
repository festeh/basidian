<script lang="ts">
	import { goto } from '$app/navigation';
	import { currentThemeName } from '$lib/stores/theme';
	import { themeList } from '$lib/themes';
	import type { ThemeName } from '$lib/types';

	function selectTheme(name: ThemeName) {
		currentThemeName.set(name);
	}

	function goBack() {
		goto('/');
	}
</script>

<div class="settings">
	<header>
		<button class="back-btn" onclick={goBack} aria-label="Go back">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
				<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
			</svg>
		</button>
		<h1>Settings</h1>
	</header>

	<main>
		<section>
			<h2>Appearance</h2>
			<div class="theme-grid">
				{#each themeList as theme}
					<button
						class="theme-card"
						class:selected={$currentThemeName === theme.name}
						onclick={() => selectTheme(theme.name as ThemeName)}
					>
						<div class="preview-colors">
							<div class="color" style="background-color: {theme.colors.base}"></div>
							<div class="color" style="background-color: {theme.colors.accent}"></div>
							<div class="color" style="background-color: {theme.colors.secondary}"></div>
						</div>
						<div class="theme-info">
							<span class="theme-name">{theme.displayName}</span>
							<span class="theme-type">{theme.isDark ? 'Dark' : 'Light'}</span>
						</div>
						{#if $currentThemeName === theme.name}
							<svg class="check" width="24" height="24" viewBox="0 0 24 24" fill="var(--color-accent)"
								>
								<path
									d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
								/>
							</svg>
						{/if}
					</button>
				{/each}
			</div>
		</section>
	</main>
</div>

<style>
	.settings {
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

	section h2 {
		font-size: 16px;
		color: var(--color-accent);
		margin-bottom: 16px;
	}

	.theme-grid {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.theme-card {
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 16px;
		background-color: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: 12px;
		cursor: pointer;
		text-align: left;
	}

	.theme-card:hover {
		background-color: var(--color-overlay);
	}

	.theme-card.selected {
		border-color: var(--color-accent);
		border-width: 2px;
	}

	.preview-colors {
		display: flex;
		gap: 4px;
	}

	.color {
		width: 24px;
		height: 24px;
		border-radius: 4px;
		border: 1px solid var(--color-overlay);
	}

	.theme-info {
		flex: 1;
		display: flex;
		flex-direction: column;
	}

	.theme-name {
		font-weight: 500;
		color: var(--color-text);
	}

	.theme-type {
		font-size: 12px;
		color: var(--color-subtext);
	}

	.check {
		flex-shrink: 0;
	}
</style>
