/**
 * AI Chat Plugin - Chutes Provider
 *
 * Implements the AIProvider interface for Chutes AI.
 * Uses OpenAI-compatible API at https://llm.chutes.ai/v1
 */

import type {
  AIProvider,
  Message,
  SendMessageOptions,
  ProviderConfig,
  ChatCompletionResponse,
} from '../types';

export class ChutesProvider implements AIProvider {
  readonly id: string;
  readonly name: string;
  readonly config: ProviderConfig;

  constructor(config: ProviderConfig) {
    this.id = config.id;
    this.name = config.name;
    this.config = config;
  }

  /**
   * Send messages to Chutes AI and get a response.
   * Supports streaming via onChunk callback.
   */
  async sendMessage(
    messages: Message[],
    options: SendMessageOptions,
    onChunk?: (chunk: string) => void
  ): Promise<string> {
    const { apiKey, model, temperature = 0.7, maxTokens = 1024 } = options;
    const useStreaming = options.stream !== false && onChunk !== undefined;

    const requestBody = {
      model,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      stream: useStreaming,
      temperature,
      max_tokens: maxTokens,
    };

    const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chutes API error (${response.status}): ${errorText}`);
    }

    if (useStreaming) {
      return this.handleStreamingResponse(response, onChunk!);
    } else {
      return this.handleNonStreamingResponse(response);
    }
  }

  /**
   * Handle streaming response using ReadableStream.
   */
  private async handleStreamingResponse(
    response: Response,
    onChunk: (chunk: string) => void
  ): Promise<string> {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            // Skip [DONE] marker
            if (data === '[DONE]') continue;

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices?.[0]?.delta?.content;
              if (content) {
                fullContent += content;
                onChunk(content);
              }
            } catch {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

    return fullContent;
  }

  /**
   * Handle non-streaming response.
   */
  private async handleNonStreamingResponse(response: Response): Promise<string> {
    const data: ChatCompletionResponse = await response.json();
    return data.choices[0]?.message?.content ?? '';
  }

  /**
   * Validate an API key by making a minimal request.
   */
  async validateApiKey(apiKey: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });

      return response.ok;
    } catch {
      return false;
    }
  }
}
