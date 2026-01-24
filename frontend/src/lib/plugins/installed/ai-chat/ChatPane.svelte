<script lang="ts">
  import { untrack } from 'svelte';
  import { closeChatPane, getContext } from './index';
  import { getProvider } from './providers';
  import {
    getSettings,
    getConversations,
    getConversation,
    saveConversation,
    deleteConversation,
    getCurrentConversationId,
    setCurrentConversationId,
    createConversation,
    createMessageId,
    generateTitle,
  } from './storage';
  import type { Conversation, Message, AISettings } from './types';
  import ChatMessage from './ChatMessage.svelte';

  // State
  let conversations = $state<Conversation[]>([]);
  let currentConversation = $state<Conversation | null>(null);
  let inputText = $state('');
  let isLoading = $state(false);
  let errorMessage = $state<string | null>(null);
  let showConversationList = $state(false);
  let messagesContainer: HTMLDivElement | undefined = $state();

  // Load conversations on mount
  $effect(() => {
    untrack(() => {
      const log = getContext()?.log;
      log?.info('ChatPane mounted');
      loadConversations();
      log?.debug('ChatPane loadConversations completed');
    });
  });

  // Auto-scroll to bottom when messages change
  $effect(() => {
    if (currentConversation?.messages && messagesContainer) {
      scrollToBottom();
    }
  });

  function loadConversations() {
    conversations = getConversations();
    const currentId = getCurrentConversationId();

    if (currentId) {
      currentConversation = getConversation(currentId);
    }

    // Create new conversation if none exists or current not found
    if (!currentConversation) {
      startNewConversation();
    }
  }

  function startNewConversation() {
    currentConversation = createConversation();
    saveConversation(currentConversation);
    setCurrentConversationId(currentConversation.id);
    conversations = getConversations();
  }

  function selectConversation(conv: Conversation) {
    currentConversation = conv;
    setCurrentConversationId(conv.id);
    showConversationList = false;
  }

  function handleDeleteConversation(id: string) {
    if (confirm('Delete this conversation?')) {
      deleteConversation(id);
      conversations = getConversations();

      if (currentConversation?.id === id) {
        if (conversations.length > 0) {
          selectConversation(conversations[0]);
        } else {
          startNewConversation();
        }
      }
    }
  }

  function scrollToBottom() {
    if (messagesContainer) {
      requestAnimationFrame(() => {
        messagesContainer!.scrollTop = messagesContainer!.scrollHeight;
      });
    }
  }

  async function sendMessage() {
    if (!inputText.trim() || isLoading) return;

    const settings = getSettings();

    // Check for API key
    if (!settings.apiKey) {
      errorMessage = 'Please configure your API key in Settings → AI Chat';
      return;
    }

    // Get provider
    const provider = getProvider(settings.provider);
    if (!provider) {
      errorMessage = `Provider "${settings.provider}" not found`;
      return;
    }

    // Clear any previous error
    errorMessage = null;

    // Ensure we have a conversation
    if (!currentConversation) {
      startNewConversation();
    }

    // Create user message
    const userMessage: Message = {
      id: createMessageId(currentConversation!.messages.length),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toISOString(),
      status: 'sending',
    };

    // Add user message to conversation
    currentConversation!.messages = [...currentConversation!.messages, userMessage];

    // Auto-generate title from first message
    if (!currentConversation!.title) {
      currentConversation!.title = generateTitle(userMessage.content);
    }

    // Clear input
    const messageContent = inputText.trim();
    inputText = '';

    // Create placeholder for assistant response
    const assistantMessage: Message = {
      id: createMessageId(currentConversation!.messages.length),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };

    currentConversation!.messages = [...currentConversation!.messages, assistantMessage];

    // Save and update
    currentConversation!.updatedAt = new Date().toISOString();
    saveConversation(currentConversation!);

    isLoading = true;

    try {
      // Build messages array for API
      const apiMessages = currentConversation!.messages
        .filter((m) => m.role !== 'assistant' || m.content)
        .slice(0, -1); // Exclude empty assistant placeholder

      // Add system prompt if configured
      if (settings.systemPrompt) {
        apiMessages.unshift({
          id: 'system',
          role: 'system' as const,
          content: settings.systemPrompt,
          timestamp: new Date().toISOString(),
        });
      }

      // Send message with streaming
      await provider.sendMessage(
        apiMessages,
        {
          apiKey: settings.apiKey,
          model: settings.model,
          temperature: settings.temperature,
          maxTokens: settings.maxTokens,
          stream: true,
        },
        (chunk) => {
          // Update assistant message content with streaming chunk
          const lastIdx = currentConversation!.messages.length - 1;
          const updatedMessages = [...currentConversation!.messages];
          updatedMessages[lastIdx] = {
            ...updatedMessages[lastIdx],
            content: updatedMessages[lastIdx].content + chunk,
          };
          currentConversation!.messages = updatedMessages;
        }
      );

      // Mark user message as sent
      const userIdx = currentConversation!.messages.length - 2;
      const updatedMessages = [...currentConversation!.messages];
      updatedMessages[userIdx] = { ...updatedMessages[userIdx], status: 'sent' };
      currentConversation!.messages = updatedMessages;

      // Save final state
      currentConversation!.updatedAt = new Date().toISOString();
      saveConversation(currentConversation!);
      conversations = getConversations();
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Unknown error';

      // Mark user message as error
      const userIdx = currentConversation!.messages.length - 2;
      const updatedMessages = [...currentConversation!.messages];
      updatedMessages[userIdx] = {
        ...updatedMessages[userIdx],
        status: 'error',
        error,
      };

      // Remove empty assistant message
      updatedMessages.pop();
      currentConversation!.messages = updatedMessages;

      errorMessage = error;
      saveConversation(currentConversation!);
    } finally {
      isLoading = false;
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
    if (event.key === 'Escape') {
      closeChatPane();
    }
  }

  function retryLastMessage() {
    if (!currentConversation || currentConversation.messages.length === 0) return;

    // Find last user message with error
    const lastUserIdx = currentConversation.messages.findLastIndex(
      (m) => m.role === 'user' && m.status === 'error'
    );

    if (lastUserIdx >= 0) {
      // Get the message content and remove the failed message
      const failedMessage = currentConversation.messages[lastUserIdx];
      currentConversation.messages = currentConversation.messages.slice(0, lastUserIdx);
      saveConversation(currentConversation);

      // Resend
      inputText = failedMessage.content;
      errorMessage = null;
      sendMessage();
    }
  }

  function dismissError() {
    errorMessage = null;
  }
</script>

<div class="chat-pane">
  <header class="chat-header">
    <div class="header-left">
      <button
        class="icon-button"
        onclick={() => (showConversationList = !showConversationList)}
        title="Conversations"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <h3 class="chat-title">{currentConversation?.title ?? 'New Chat'}</h3>
    </div>
    <div class="header-right">
      <button class="icon-button" onclick={startNewConversation} title="New Conversation">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </button>
      <button class="icon-button" onclick={closeChatPane} title="Close">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  </header>

  <!-- Conversation list sidebar -->
  {#if showConversationList}
    <div class="conversation-list">
      <div class="conversation-list-header">
        <span>Conversations</span>
      </div>
      <div class="conversation-list-items">
        {#each conversations as conv (conv.id)}
          <div
            class="conversation-item"
            class:active={conv.id === currentConversation?.id}
            onclick={() => selectConversation(conv)}
            onkeydown={(e) => e.key === 'Enter' && selectConversation(conv)}
            role="button"
            tabindex="0"
          >
            <span class="conversation-title">{conv.title ?? 'New Chat'}</span>
            <button
              class="delete-button"
              onclick={(e) => {
                e.stopPropagation();
                handleDeleteConversation(conv.id);
              }}
              title="Delete"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>
        {/each}
        {#if conversations.length === 0}
          <div class="empty-list">No conversations yet</div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Messages area -->
  <div class="messages" bind:this={messagesContainer}>
    {#if currentConversation && currentConversation.messages.length > 0}
      {#each currentConversation.messages as message, idx (message.id)}
        <ChatMessage
          {message}
          isStreaming={isLoading && idx === currentConversation.messages.length - 1 && message.role === 'assistant'}
        />
      {/each}
    {:else}
      <div class="empty-state">
        <p>Start a conversation with AI</p>
        <p class="hint">Type a message below to begin</p>
      </div>
    {/if}
  </div>

  <!-- Error message -->
  {#if errorMessage}
    <div class="error-banner">
      <span>{errorMessage}</span>
      <div class="error-actions">
        <button onclick={retryLastMessage}>Retry</button>
        <button onclick={dismissError}>Dismiss</button>
      </div>
    </div>
  {/if}

  <!-- Input area -->
  <div class="input-area">
    <textarea
      bind:value={inputText}
      onkeydown={handleKeydown}
      placeholder="Type a message..."
      disabled={isLoading}
      rows="1"
    ></textarea>
    <button
      class="send-button"
      onclick={sendMessage}
      disabled={!inputText.trim() || isLoading}
      title="Send message"
    >
      {#if isLoading}
        <svg class="spinner" width="18" height="18" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="32" stroke-linecap="round" />
        </svg>
      {:else}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      {/if}
    </button>
  </div>
</div>

<style>
  .chat-pane {
    position: fixed;
    top: 0;
    right: 0;
    width: 380px;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--color-base);
    border-left: 1px solid var(--color-overlay);
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
  }

  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-overlay);
    background: var(--color-mantle);
  }

  .header-left,
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .chat-title {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 180px;
  }

  .icon-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--color-subtext);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .icon-button:hover {
    background: var(--color-surface);
    color: var(--color-text);
  }

  /* Conversation list */
  .conversation-list {
    position: absolute;
    top: 52px;
    left: 0;
    width: 100%;
    max-height: 300px;
    background: var(--color-base);
    border-bottom: 1px solid var(--color-overlay);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 10;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .conversation-list-header {
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    color: var(--color-subtext);
    border-bottom: 1px solid var(--color-overlay);
  }

  .conversation-list-items {
    overflow-y: auto;
    max-height: 250px;
  }

  .conversation-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .conversation-item:hover {
    background: var(--color-surface);
  }

  .conversation-item.active {
    background: var(--color-overlay);
  }

  .conversation-title {
    font-size: 13px;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
  }

  .delete-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--color-subtext);
    cursor: pointer;
    opacity: 0;
    transition: all 0.15s ease;
  }

  .conversation-item:hover .delete-button {
    opacity: 1;
  }

  .delete-button:hover {
    background: rgba(243, 139, 168, 0.2);
    color: var(--color-error);
  }

  .empty-list {
    padding: 20px;
    text-align: center;
    font-size: 13px;
    color: var(--color-subtext);
  }

  /* Messages */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: var(--color-subtext);
  }

  .empty-state p {
    margin: 0;
  }

  .empty-state .hint {
    font-size: 12px;
    margin-top: 4px;
  }

  /* Error banner */
  .error-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background: rgba(243, 139, 168, 0.15);
    border-top: 1px solid var(--color-error);
    font-size: 13px;
    color: var(--color-error);
  }

  .error-actions {
    display: flex;
    gap: 8px;
  }

  .error-actions button {
    padding: 4px 10px;
    border: none;
    border-radius: 4px;
    background: var(--color-error);
    color: var(--color-base);
    font-size: 12px;
    cursor: pointer;
    transition: opacity 0.15s ease;
  }

  .error-actions button:hover {
    opacity: 0.9;
  }

  /* Input area */
  .input-area {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid var(--color-overlay);
    background: var(--color-mantle);
  }

  .input-area textarea {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid var(--color-overlay);
    border-radius: 8px;
    background: var(--color-surface);
    color: var(--color-text);
    font-size: 14px;
    font-family: inherit;
    resize: none;
    min-height: 40px;
    max-height: 120px;
    outline: none;
    transition: border-color 0.15s ease;
  }

  .input-area textarea:focus {
    border-color: var(--color-accent);
  }

  .input-area textarea:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .send-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    padding: 0;
    border: none;
    border-radius: 8px;
    background: var(--color-accent);
    color: var(--color-base);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .send-button:hover:not(:disabled) {
    filter: brightness(1.1);
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  /* Responsive */
  @media (max-width: 480px) {
    .chat-pane {
      width: 100%;
    }
  }
</style>
