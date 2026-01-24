<script lang="ts">
  import { toggleChatPane, chatPaneOpen, getContext } from './index';
  import ChatPane from './ChatPane.svelte';

  let isOpen = $state(false);

  // Subscribe to chat pane state
  $effect(() => {
    const log = getContext()?.log;
    log?.debug('ChatButton effect running');
    const unsubscribe = chatPaneOpen.subscribe((value) => {
      log?.debug('chatPaneOpen changed', { value });
      isOpen = value;
    });
    return unsubscribe;
  });

  function handleClick() {
    const log = getContext()?.log;
    log?.info('AI Chat button clicked');
    toggleChatPane();
    log?.info('AI Chat toggleChatPane completed');
  }
</script>

<button
  class="chat-button"
  class:active={isOpen}
  onclick={handleClick}
  title="AI Chat"
  aria-label="Toggle AI Chat"
>
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <!-- Chat bubble icon -->
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    <!-- AI sparkle -->
    <circle cx="9" cy="10" r="1" fill="currentColor" />
    <circle cx="12" cy="10" r="1" fill="currentColor" />
    <circle cx="15" cy="10" r="1" fill="currentColor" />
  </svg>
</button>

<!-- Render chat pane when open -->
{#if isOpen}
  <ChatPane />
{/if}

<style>
  .chat-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--color-subtext);
    cursor: pointer;
    transition: all 0.15s;
  }

  .chat-button:hover {
    background: var(--color-surface);
    color: var(--color-text);
  }

  .chat-button.active {
    background: var(--color-accent, #007aff);
    color: white;
  }

  .chat-button svg {
    flex-shrink: 0;
  }
</style>
