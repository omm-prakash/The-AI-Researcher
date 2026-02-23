<script setup>
import { nextTick, watch } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  messages: Array,
  isWaiting: Boolean
})

watch(() => props.messages.length, async () => {
    await nextTick();
    const container = document.getElementById('chat-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
});

const renderMarkdown = (content) => {
    return marked(content || '');
}
</script>

<template>
  <div class="messages">
    <div v-if="messages.length === 0" class="empty-state">
      <div class="logo-placeholder">✨</div>
      <h2>How can I help you research today?</h2>
      <p>Ask a complex query, attach a PDF, or record an audio message.</p>
    </div>
    
    <div 
      v-for="msg in messages" 
      :key="msg.id" 
      :class="['message-wrapper', msg.role]"
    >
      <div class="message-content markdown-body" v-html="renderMarkdown(msg.content)"></div>
      <div v-if="msg.attachments && msg.attachments.length" class="attachments">
          <span v-for="(file, idx) in msg.attachments" :key="idx" class="attachment-badge">
              📎 {{ file.name }}
          </span>
      </div>
    </div>
    
    <div v-if="isWaiting" class="message-wrapper assistant">
      <div class="message-content typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  text-align: center;
  margin-top: 4rem;
}
.logo-placeholder {
  font-size: 3rem;
  margin-bottom: 1rem;
}
.empty-state h2 {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 85%;
  animation: fadeIn 0.3s ease-out forwards;
}

.message-wrapper.user {
  align-self: flex-end;
}

.message-wrapper.assistant,
.message-wrapper.system {
  align-self: flex-start;
}

.message-content {
  padding: 1rem 1.25rem;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 0.95rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.user .message-content {
  background: var(--accent);
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant .message-content {
  background: var(--glass-bg);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.system .message-content {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.attachments {
    margin-top: 0.5rem;
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.attachment-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.6rem;
    background: rgba(0,0,0,0.2);
    border-radius: 12px;
    border: 1px solid var(--border);
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 1.25rem 1.5rem !important;
  align-items: center;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  background-color: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Make markdown inside message content more readable */
:deep(.markdown-body p) {
    margin: 0 0 1em 0;
}
:deep(.markdown-body p:last-child) {
    margin-bottom: 0;
}
:deep(.markdown-body ul), :deep(.markdown-body ol) {
    margin: 0.5em 0;
    padding-left: 1.5em;
}
</style>
