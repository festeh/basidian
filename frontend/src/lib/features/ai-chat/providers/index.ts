/**
 * AI Chat - Provider Registry
 *
 * Exports provider interface and manages provider instances.
 */

import type { AIProvider, ProviderConfig } from '../types';
import { PROVIDERS } from '../types';
import { ChutesProvider } from './chutes';

// Re-export types for convenience
export type { AIProvider, ProviderConfig };

// Provider instances
const providerInstances: Map<string, AIProvider> = new Map();

/**
 * Get a provider instance by ID.
 * Creates the instance on first access.
 */
export function getProvider(providerId: string): AIProvider | null {
  // Return cached instance if exists
  if (providerInstances.has(providerId)) {
    return providerInstances.get(providerId)!;
  }

  // Create new instance based on provider ID
  const config = PROVIDERS[providerId];
  if (!config) {
    return null;
  }

  let provider: AIProvider;

  switch (providerId) {
    case 'chutes':
      provider = new ChutesProvider(config);
      break;
    default:
      return null;
  }

  providerInstances.set(providerId, provider);
  return provider;
}

/**
 * Get all available provider configurations.
 */
export function getAvailableProviders(): ProviderConfig[] {
  return Object.values(PROVIDERS);
}

/**
 * Get a provider configuration by ID.
 */
export function getProviderConfig(providerId: string): ProviderConfig | null {
  return PROVIDERS[providerId] ?? null;
}
