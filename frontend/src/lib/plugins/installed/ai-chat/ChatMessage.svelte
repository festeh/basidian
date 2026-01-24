<script lang="ts">
  import type { Message } from './types';

  interface Props {
    message: Message;
    isStreaming?: boolean;
  }

  let { message, isStreaming = false }: Props = $props();

  // Format timestamp for display
  function formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class="message" class:user={message.role === 'user'} class:assistant={message.role === 'assistant'}>
  <div class="message-content">
    {#if message.role === 'assistant' && isStreaming && !message.content}
      <span class="typing-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </span>
    {:else}
      <p>{message.content}</p>
    {/if}
  </div>
  <div class="message-meta">
    <span class="timestamp">{formatTime(message.timestamp)}</span>
    {#if message.status === 'error'}
      <span class="error-badge" title={message.error}>Error</span>
    {/if}
  </div>
</div>

<style>
  .message {
    display: flex;
    flex-direction: column;
    max-width: 85%;
    margin-bottom: 12px;
  }

  .message.user {
    align-self: flex-end;
  }

  .message.assistant {
    align-self: flex-start;
  }

  .message-content {
    padding: 10px 14px;
    border-radius: 12px;
    word-wrap: break-word;
    white-space: pre-wrap;
  }

  .message.user .message-content {
    background: var(--color-accent);
    color: var(--color-base);
    border-bottom-right-radius: 4px;
  }

  .message.assistant .message-content {
    background: var(--color-surface);
    color: var(--color-text);
    border-bottom-left-radius: 4px;
  }

  .message-content p {
    margin: 0;
    line-height: 1.4;
  }

  .message-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
    padding: 0 4px;
  }

  .message.user .message-meta {
    justify-content: flex-end;
  }

  .timestamp {
    font-size: 11px;
    color: var(--color-subtext);
  }

  .error-badge {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--color-error);
    color: var(--color-base);
  }

  /* Typing indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 4px 0;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-subtext);
    animation: typing 1.4s infinite ease-in-out;
  }

  .dot:nth-child(2) {
    animation-delay: 0.2s;
  }

  .dot:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
      opacity: 0.4;
    }
    30% {
      transform: translateY(-4px);
      opacity: 1;
    }
  }
</style>
