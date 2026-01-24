<script lang="ts">
  import { getSettings, saveSettings } from './storage';
  import { getProvider, getAvailableProviders } from './providers';
  import type { AISettings, ProviderConfig } from './types';
  import { PROVIDERS } from './types';

  // State
  let settings = $state<AISettings>(getSettings());
  let showApiKey = $state(false);
  let isValidating = $state(false);
  let validationResult = $state<'valid' | 'invalid' | null>(null);

  // Available providers
  const providers = getAvailableProviders();

  // Get current provider config
  let currentProvider = $derived(PROVIDERS[settings.provider]);
  let availableModels = $derived(currentProvider?.models ?? []);

  // Auto-save when settings change
  function updateSettings(updates: Partial<AISettings>) {
    settings = { ...settings, ...updates };
    saveSettings(settings);
    // Clear validation result when API key changes
    if ('apiKey' in updates) {
      validationResult = null;
    }
  }

  function handleProviderChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const providerId = target.value;
    const providerConfig = PROVIDERS[providerId];

    updateSettings({
      provider: providerId,
      model: providerConfig?.defaultModel ?? '',
      apiKey: null, // Clear API key when switching providers
    });
    validationResult = null;
  }

  function handleModelChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    updateSettings({ model: target.value });
  }

  function handleApiKeyInput(event: Event) {
    const target = event.target as HTMLInputElement;
    updateSettings({ apiKey: target.value || null });
  }

  function handleTemperatureInput(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseFloat(target.value);
    updateSettings({ temperature: Math.min(2, Math.max(0, value)) });
  }

  function handleMaxTokensInput(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value, 10);
    updateSettings({ maxTokens: Math.min(4096, Math.max(1, value || 1024)) });
  }

  function handleSystemPromptInput(event: Event) {
    const target = event.target as HTMLTextAreaElement;
    updateSettings({ systemPrompt: target.value || null });
  }

  async function validateApiKey() {
    if (!settings.apiKey) {
      validationResult = 'invalid';
      return;
    }

    const provider = getProvider(settings.provider);
    if (!provider) {
      validationResult = 'invalid';
      return;
    }

    isValidating = true;
    validationResult = null;

    try {
      const isValid = await provider.validateApiKey(settings.apiKey);
      validationResult = isValid ? 'valid' : 'invalid';
    } catch {
      validationResult = 'invalid';
    } finally {
      isValidating = false;
    }
  }

  function toggleShowApiKey() {
    showApiKey = !showApiKey;
  }
</script>

<div class="settings">
  <!-- Provider Selection -->
  <div class="setting-group">
    <label for="provider">AI Provider</label>
    <select id="provider" value={settings.provider} onchange={handleProviderChange}>
      {#each providers as provider (provider.id)}
        <option value={provider.id}>{provider.name}</option>
      {/each}
    </select>
  </div>

  <!-- API Key -->
  <div class="setting-group">
    <label for="apiKey">API Key</label>
    <div class="api-key-input">
      <input
        id="apiKey"
        type={showApiKey ? 'text' : 'password'}
        value={settings.apiKey ?? ''}
        oninput={handleApiKeyInput}
        placeholder="Enter your API key"
      />
      <button class="toggle-visibility" onclick={toggleShowApiKey} type="button" title={showApiKey ? 'Hide' : 'Show'}>
        {#if showApiKey}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
            <line x1="1" y1="1" x2="23" y2="23" />
          </svg>
        {:else}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        {/if}
      </button>
    </div>
    <div class="api-key-actions">
      <button
        class="validate-button"
        onclick={validateApiKey}
        disabled={!settings.apiKey || isValidating}
      >
        {isValidating ? 'Validating...' : 'Validate Key'}
      </button>
      {#if validationResult === 'valid'}
        <span class="validation-badge valid">✓ Valid</span>
      {:else if validationResult === 'invalid'}
        <span class="validation-badge invalid">✗ Invalid</span>
      {/if}
    </div>
    <p class="setting-hint">
      Get your API key from <a href="https://chutes.ai" target="_blank" rel="noopener">chutes.ai</a>
    </p>
  </div>

  <!-- Model Selection -->
  <div class="setting-group">
    <label for="model">Model</label>
    <select id="model" value={settings.model} onchange={handleModelChange}>
      {#each availableModels as model (model)}
        <option value={model}>{model}</option>
      {/each}
    </select>
  </div>

  <!-- Temperature -->
  <div class="setting-group">
    <label for="temperature">
      Temperature
      <span class="value-display">{settings.temperature.toFixed(1)}</span>
    </label>
    <input
      id="temperature"
      type="range"
      min="0"
      max="2"
      step="0.1"
      value={settings.temperature}
      oninput={handleTemperatureInput}
    />
    <p class="setting-hint">
      Lower = more focused, Higher = more creative
    </p>
  </div>

  <!-- Max Tokens -->
  <div class="setting-group">
    <label for="maxTokens">Max Response Length</label>
    <input
      id="maxTokens"
      type="number"
      min="1"
      max="4096"
      value={settings.maxTokens}
      oninput={handleMaxTokensInput}
    />
    <p class="setting-hint">Maximum tokens in AI response (1-4096)</p>
  </div>

  <!-- System Prompt -->
  <div class="setting-group">
    <label for="systemPrompt">System Prompt (Optional)</label>
    <textarea
      id="systemPrompt"
      value={settings.systemPrompt ?? ''}
      oninput={handleSystemPromptInput}
      placeholder="Custom instructions for the AI..."
      rows="3"
    ></textarea>
    <p class="setting-hint">
      Customize the AI's behavior with a system prompt
    </p>
  </div>
</div>

<style>
  .settings {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .setting-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .setting-group label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text);
  }

  .value-display {
    font-weight: normal;
    color: var(--color-subtext);
  }

  .setting-group select,
  .setting-group input[type="text"],
  .setting-group input[type="password"],
  .setting-group input[type="number"],
  .setting-group textarea {
    padding: 8px 12px;
    border: 1px solid var(--color-overlay);
    border-radius: 6px;
    background: var(--color-surface);
    color: var(--color-text);
    font-size: 14px;
    font-family: inherit;
    outline: none;
    transition: border-color 0.15s ease;
  }

  .setting-group select:focus,
  .setting-group input:focus,
  .setting-group textarea:focus {
    border-color: var(--color-accent);
  }

  .setting-group input[type="range"] {
    width: 100%;
    cursor: pointer;
  }

  .setting-group textarea {
    resize: vertical;
    min-height: 60px;
  }

  .setting-hint {
    margin: 0;
    font-size: 12px;
    color: var(--color-subtext);
  }

  .setting-hint a {
    color: var(--color-accent);
    text-decoration: none;
  }

  .setting-hint a:hover {
    text-decoration: underline;
  }

  /* API Key Input */
  .api-key-input {
    display: flex;
    gap: 4px;
  }

  .api-key-input input {
    flex: 1;
  }

  .toggle-visibility {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    padding: 0;
    border: 1px solid var(--color-overlay);
    border-radius: 6px;
    background: var(--color-surface);
    color: var(--color-subtext);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .toggle-visibility:hover {
    background: var(--color-overlay);
    color: var(--color-text);
  }

  .api-key-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 4px;
  }

  .validate-button {
    padding: 6px 12px;
    border: none;
    border-radius: 6px;
    background: var(--color-accent);
    color: var(--color-base);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.15s ease;
  }

  .validate-button:hover:not(:disabled) {
    filter: brightness(1.1);
  }

  .validate-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .validation-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .validation-badge.valid {
    background: rgba(166, 227, 161, 0.2);
    color: var(--color-success);
  }

  .validation-badge.invalid {
    background: rgba(243, 139, 168, 0.2);
    color: var(--color-error);
  }
</style>
