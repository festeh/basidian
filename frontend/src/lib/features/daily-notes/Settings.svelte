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

	label {
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

	.hint {
		font-size: 11px;
		color: var(--color-subtext);
	}
</style>
