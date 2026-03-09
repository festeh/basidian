<script lang="ts">
	import { versions, selectedVersion, historyActions, historyLoading } from '$lib/stores/history';

	interface Props {
		currentContent: string;
	}

	let { currentContent }: Props = $props();

	function formatRelativeTime(isoString: string): string {
		const date = new Date(isoString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffSec = Math.floor(diffMs / 1000);
		const diffMin = Math.floor(diffSec / 60);
		const diffHour = Math.floor(diffMin / 60);
		const diffDay = Math.floor(diffHour / 24);

		if (diffSec < 60) return 'just now';
		if (diffMin < 60) return `${diffMin}m ago`;
		if (diffHour < 24) return `${diffHour}h ago`;
		if (diffDay === 1) return 'yesterday';
		if (diffDay < 7) return `${diffDay}d ago`;
		return date.toLocaleDateString();
	}

	function computeDiffLines(
		oldContent: string,
		newContent: string
	): { type: 'same' | 'added' | 'removed'; text: string }[] {
		const oldLines = oldContent.split('\n');
		const newLines = newContent.split('\n');
		const result: { type: 'same' | 'added' | 'removed'; text: string }[] = [];

		// Simple LCS-based diff
		const m = oldLines.length;
		const n = newLines.length;

		// Build LCS table
		const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
		for (let i = 1; i <= m; i++) {
			for (let j = 1; j <= n; j++) {
				if (oldLines[i - 1] === newLines[j - 1]) {
					dp[i][j] = dp[i - 1][j - 1] + 1;
				} else {
					dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
				}
			}
		}

		// Backtrack to build diff
		const diff: { type: 'same' | 'added' | 'removed'; text: string }[] = [];
		let i = m,
			j = n;
		while (i > 0 || j > 0) {
			if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
				diff.push({ type: 'same', text: oldLines[i - 1] });
				i--;
				j--;
			} else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
				diff.push({ type: 'added', text: newLines[j - 1] });
				j--;
			} else {
				diff.push({ type: 'removed', text: oldLines[i - 1] });
				i--;
			}
		}

		diff.reverse();
		return diff;
	}

	let diffLines = $derived.by(() => {
		if (!$selectedVersion) return [];
		return computeDiffLines($selectedVersion.content, currentContent);
	});
</script>

<div class="history-panel">
	<div class="history-header">
		<span class="history-title">History</span>
		<button class="close-btn" onclick={() => historyActions.close()} title="Close history">
			<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
				<path
					d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
				/>
			</svg>
		</button>
	</div>

	{#if $historyLoading}
		<div class="history-empty">Loading...</div>
	{:else if $selectedVersion}
		<div class="version-detail">
			<div class="version-detail-header">
				<button class="back-btn" onclick={() => selectedVersion.set(null)}>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
						<path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
					</svg>
					Back
				</button>
				<button class="restore-btn" onclick={() => historyActions.restore($selectedVersion!.id)}>
					Restore
				</button>
			</div>
			<div class="diff-view">
				{#each diffLines as line}
					<div
						class="diff-line"
						class:diff-added={line.type === 'added'}
						class:diff-removed={line.type === 'removed'}
					>
						<span class="diff-marker"
							>{line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}</span
						>
						<span class="diff-text">{line.text || '\u00A0'}</span>
					</div>
				{/each}
			</div>
		</div>
	{:else if $versions.length === 0}
		<div class="history-empty">No previous versions yet</div>
	{:else}
		<div class="version-list">
			{#each $versions as version}
				<button
					class="version-item"
					onclick={() => historyActions.selectVersion(version.id)}
				>
					<span class="version-time">{formatRelativeTime(version.created_at)}</span>
					<span class="version-summary">
						{#if version.lines_added > 0}
							<span class="stat-added">+{version.lines_added}</span>
						{/if}
						{#if version.lines_removed > 0}
							<span class="stat-removed">-{version.lines_removed}</span>
						{/if}
						{#if version.lines_added === 0 && version.lines_removed === 0}
							<span class="stat-none">no changes</span>
						{/if}
					</span>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.history-panel {
		width: 300px;
		min-width: 300px;
		border-left: 1px solid var(--color-overlay);
		display: flex;
		flex-direction: column;
		background-color: var(--color-mantle);
		overflow: hidden;
	}

	.history-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-compact) var(--space-comfortable);
		border-bottom: 1px solid var(--color-overlay);
	}

	.history-title {
		font-weight: 600;
		font-size: var(--text-body);
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: none;
		background: transparent;
		color: var(--color-subtext);
		border-radius: var(--radius-default);
		cursor: pointer;
	}

	.close-btn:hover {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.history-empty {
		padding: var(--space-comfortable);
		color: var(--color-subtext);
		text-align: center;
		font-size: var(--text-detail);
	}

	.version-list {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-compact);
	}

	.version-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: var(--space-compact) var(--space-cozy);
		border: none;
		background: transparent;
		color: var(--color-text);
		font-size: var(--text-detail);
		border-radius: var(--radius-default);
		cursor: pointer;
		text-align: left;
	}

	.version-item:hover {
		background-color: var(--color-overlay);
	}

	.version-time {
		color: var(--color-subtext);
	}

	.version-summary {
		display: flex;
		gap: var(--space-snug);
		font-size: var(--text-detail);
		font-family: monospace;
	}

	.stat-added {
		color: var(--color-success);
	}

	.stat-removed {
		color: var(--color-error);
	}

	.stat-none {
		color: var(--color-subtext);
	}

	.version-detail {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.version-detail-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-compact) var(--space-cozy);
		border-bottom: 1px solid var(--color-overlay);
	}

	.back-btn {
		display: flex;
		align-items: center;
		gap: var(--space-snug);
		border: none;
		background: transparent;
		color: var(--color-subtext);
		font-size: var(--text-detail);
		cursor: pointer;
		padding: var(--space-snug) var(--space-compact);
		border-radius: var(--radius-default);
	}

	.back-btn:hover {
		background-color: var(--color-overlay);
		color: var(--color-text);
	}

	.restore-btn {
		border: none;
		background-color: var(--color-accent);
		color: var(--color-base);
		font-size: var(--text-detail);
		font-weight: 500;
		padding: var(--space-snug) var(--space-cozy);
		border-radius: var(--radius-default);
		cursor: pointer;
	}

	.restore-btn:hover {
		opacity: 0.9;
	}

	.diff-view {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-compact);
		font-family: monospace;
		font-size: var(--text-detail);
		line-height: 1.5;
	}

	.diff-line {
		display: flex;
		white-space: pre-wrap;
		word-break: break-all;
	}

	.diff-added {
		background-color: color-mix(in srgb, var(--color-success) 15%, transparent);
	}

	.diff-removed {
		background-color: color-mix(in srgb, var(--color-error) 15%, transparent);
	}

	.diff-marker {
		flex-shrink: 0;
		width: 1.5em;
		text-align: center;
		color: var(--color-subtext);
		user-select: none;
	}

	.diff-added .diff-marker {
		color: var(--color-success);
	}

	.diff-removed .diff-marker {
		color: var(--color-error);
	}

	.diff-text {
		flex: 1;
		min-width: 0;
	}
</style>
