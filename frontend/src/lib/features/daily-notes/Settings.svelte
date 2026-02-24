<script lang="ts">
	import { getSettings, saveSettings, type DailyNotesSettings } from './state';

	let settings: DailyNotesSettings = $state(getSettings());

	function handleFolderChange(e: Event) {
		const target = e.target as HTMLInputElement;
		settings.folder = target.value;
		saveSettings(settings);
	}

	function handleTemplateChange(e: Event) {
		const target = e.target as HTMLInputElement;
		settings.templatePath = target.value;
		saveSettings(settings);
	}
</script>

<div class="settings">
	<div class="setting-item">
		<label for="folder">Daily Notes Folder</label>
		<input
			type="text"
			id="folder"
			value={settings.folder}
			oninput={handleFolderChange}
			placeholder="/daily"
		/>
		<span class="hint">Folder where daily notes are stored</span>
	</div>

	<div class="setting-item">
		<span class="label" id="format-label">Date Format</span>
		<div class="format-options" role="group" aria-labelledby="format-label">
			<button
				class="format-option"
				class:selected={settings.dateFormat === 'DD-MMM-YY'}
				onclick={() => { settings.dateFormat = 'DD-MMM-YY'; saveSettings(settings); }}
			>
				DD-MMM-YY
			</button>
			<button
				class="format-option"
				class:selected={settings.dateFormat === 'YYYY-MM-DD'}
				onclick={() => { settings.dateFormat = 'YYYY-MM-DD'; saveSettings(settings); }}
			>
				YYYY-MM-DD
			</button>
			<button
				class="format-option"
				class:selected={settings.dateFormat === 'DD-MM-YYYY'}
				onclick={() => { settings.dateFormat = 'DD-MM-YYYY'; saveSettings(settings); }}
			>
				DD-MM-YYYY
			</button>
		</div>
		<span class="hint">Format for daily note filenames</span>
	</div>

	<div class="setting-item">
		<label for="template">Template Path (optional)</label>
		<input
			type="text"
			id="template"
			value={settings.templatePath}
			oninput={handleTemplateChange}
			placeholder="/templates/daily.md"
		/>
		<span class="hint">Path to template file. Use {'{{date}}'} for current date.</span>
	</div>
</div>

<style>
	.settings {
		display: flex;
		flex-direction: column;
		gap: var(--space-spacious);
	}

	.setting-item {
		display: flex;
		flex-direction: column;
		gap: var(--space-snug);
	}

	label,
	.label {
		font-size: var(--text-detail);
		font-weight: 500;
		color: var(--color-text);
	}

	input {
		padding: 10px 12px;
		background: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-default);
		color: var(--color-text);
		font-size: var(--text-detail);
	}

	input:focus {
		outline: none;
		border-color: var(--color-accent);
	}

	.format-options {
		display: flex;
		gap: var(--space-compact);
	}

	.format-option {
		flex: 1;
		padding: 10px 12px;
		background: var(--color-surface);
		border: 1px solid var(--color-overlay);
		border-radius: var(--radius-default);
		color: var(--color-subtext);
		font-size: var(--text-label);
		cursor: pointer;
		transition: all 0.15s;
	}

	.format-option:hover {
		border-color: var(--color-accent);
		color: var(--color-text);
	}

	.format-option.selected {
		background: var(--color-accent);
		border-color: var(--color-accent);
		color: var(--color-base);
		font-weight: 500;
	}

	.hint {
		font-size: 11px;
		color: var(--color-subtext);
	}
</style>
