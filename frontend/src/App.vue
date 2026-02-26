<script setup>
import { ref, computed } from 'vue'
import ChatWindow from './components/ChatWindow.vue'
import InputArea from './components/InputArea.vue'
import ConversationSidebar from './components/ConversationSidebar.vue'

const makeId = () => Math.random().toString(36).substr(2, 9)

const createConversation = () => ({
  id: makeId(),
  threadId: 'thread_' + makeId(),
  title: 'New Chat',
  messages: [],
  isWaiting: false,
})

const conversations = ref([createConversation()])
const activeId = ref(conversations.value[0].id)

const activeConv = computed(() =>
  conversations.value.find(c => c.id === activeId.value)
)

const hasMessages = computed(() =>
  (activeConv.value?.messages?.length ?? 0) > 0
)

const selectConversation = (id) => { activeId.value = id }

const newConversation = () => {
  const conv = createConversation()
  conversations.value.unshift(conv)
  activeId.value = conv.id
}

const deleteConversation = (id) => {
  const idx = conversations.value.findIndex(c => c.id === id)
  conversations.value.splice(idx, 1)
  if (conversations.value.length === 0) {
    const fresh = createConversation()
    conversations.value.push(fresh)
    activeId.value = fresh.id
  } else if (activeId.value === id) {
    activeId.value = conversations.value[Math.max(0, idx - 1)].id
  }
}

const renameConversation = ({ id, title }) => {
  const conv = conversations.value.find(c => c.id === id)
  if (conv) conv.title = title
}

// ── Re-ask: pre-fill input from an assistant message ─────────────────────────
const prefillText = ref('')
const handleReask = (content) => {
  prefillText.value = content
}

const activeController = ref(null)   // tracks in-flight fetch so it can be cancelled

const cancelRequest = () => {
  if (activeController.value) {
    activeController.value.abort()
    activeController.value = null
  }
  const target = conversations.value.find(c => c.id === activeId.value)
  if (target) target.isWaiting = false
}

const sendMessage = async (payload) => {
  const conv = activeConv.value
  if (!conv) return

  const convId = conv.id  // capture ID — used to re-lookup in finally

  conv.messages.push({
    id: Date.now(),
    role: 'user',
    content: payload.text || '📎 [File Attached]',
    attachments: payload.attachments || [],
  })

  if (conv.title === 'New Chat' && payload.text) {
    conv.title = payload.text.slice(0, 36) + (payload.text.length > 36 ? '…' : '')
  }

  conv.isWaiting = true

  // Create an AbortController so the request can be cancelled or timed out
  const controller = new AbortController()
  activeController.value = controller
  const timeoutId = setTimeout(() => controller.abort(), 90_000) // 90-second cap

  try {
    let requestOptions = {}
    if (payload.attachments && payload.attachments.length > 0) {
      const formData = new FormData()
      formData.append('thread_id', conv.threadId)
      formData.append('message', payload.text || 'Analyze attached files')
      payload.attachments.forEach(f => formData.append('files', f))
      requestOptions = { method: 'POST', body: formData, signal: controller.signal }
    } else {
      requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: conv.threadId, message: payload.text || 'Process request' }),
        signal: controller.signal,
      }
    }

    const response = await fetch('http://localhost:8000/chat', requestOptions)
    const data = await response.json()

    const target = conversations.value.find(c => c.id === convId)
    if (target) {
      target.messages.push({
        id: Date.now() + 1,
        role: response.ok ? 'assistant' : 'system',
        content: response.ok ? data.response : `**Error:** ${data.error || 'Failed to reach API'}`,
      })
    }
  } catch (err) {
    const target = conversations.value.find(c => c.id === convId)
    if (target && err.name !== 'AbortError') {
      target.messages.push({
        id: Date.now() + 1,
        role: 'system',
        content: `**Network Error:** Could not connect to API server.\n\n${err.message}`,
      })
    }
  } finally {
    clearTimeout(timeoutId)
    activeController.value = null
    // Re-lookup by ID to guarantee Vue reactivity
    const target = conversations.value.find(c => c.id === convId)
    if (target) target.isWaiting = false
  }
}
</script>

<template>
  <div class="app-shell">
    <ConversationSidebar
      :conversations="conversations"
      :activeId="activeId"
      @select="selectConversation"
      @new="newConversation"
      @delete="deleteConversation"
      @rename="renameConversation"
    />

    <div class="chat-pane">

      <!-- Header -->
      <div class="header">
        <h1>{{ activeConv?.title || 'New Chat' }}</h1>
      </div>

      <!-- Scrollable body — messages OR centered empty state -->
      <div class="chat-body" id="chat-body">

        <!-- Empty state: hero centered via flex -->
        <div v-if="!hasMessages" class="empty-center">
          <div class="empty-hero">
            <div class="hero-glyph">✦</div>
            <h2>What do you want to research?</h2>
            <p>Ask anything • Attach a PDF, image, or audio</p>
          </div>
        </div>

        <!-- Messages: scroll naturally from top -->
        <div v-else class="messages-zone">
          <ChatWindow
            :messages="activeConv?.messages || []"
            :isWaiting="activeConv?.isWaiting || false"
            @reask="handleReask"
          />
        </div>

      </div>

      <!-- Input — always pinned at bottom, outside scroll area -->
      <div class="input-bar">
        <div class="input-inner">
          <div v-if="activeConv?.isWaiting" class="cancel-row">
            <button class="cancel-btn" @click="cancelRequest">✕ Cancel</button>
          </div>
          <InputArea
            @send="sendMessage"
            :disabled="activeConv?.isWaiting || false"
            :prefill="prefillText"
            @clear-prefill="prefillText = ''"
          />
          <div class="footer-note">Assistant can make mistakes. Verify important information.</div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.empty-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-hero {
  text-align: center;
  user-select: none;
}

.hero-glyph {
  font-size: 2rem;
  margin-bottom: 0.85rem;
  color: #6060a0;
  animation: glow 3s ease-in-out infinite;
}

.empty-hero h2 {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
  font-weight: 500;
  color: #c8c8e0;
  letter-spacing: -0.01em;
}

.empty-hero p {
  margin: 0;
  font-size: 0.8rem;
  color: #7070a0;
}

@keyframes glow {
  0%, 100% { opacity: 0.35; }
  50%       { opacity: 0.9; }
}
</style>
