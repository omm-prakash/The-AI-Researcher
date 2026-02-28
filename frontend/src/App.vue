<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { supabase } from './supabase'
import ChatWindow from './components/ChatWindow.vue'
import InputArea from './components/InputArea.vue'
import ConversationSidebar from './components/ConversationSidebar.vue'
import AuthModal from './components/AuthModal.vue'

const makeId = () => Math.random().toString(36).substr(2, 9)

const createConversation = () => ({
  id: makeId(),
  threadId: 'thread_' + makeId(),
  title: 'New Chat',
  messages: [],
  isWaiting: false,
  timestamp: Date.now(),
})

const conversations = ref([])
const activeId = ref(null)

const activeConv = computed(() =>
  conversations.value.find(c => c.id === activeId.value)
)

const hasMessages = computed(() =>
  (activeConv.value?.messages?.length ?? 0) > 0
)

const sortedConversations = computed(() => {
  return [...conversations.value].sort((a, b) => {
    const tA = a.created_at ? new Date(a.created_at).getTime() : (a.timestamp || 0)
    const tB = b.created_at ? new Date(b.created_at).getTime() : (b.timestamp || 0)
    return tB - tA
  })
})

const loadHistoryForConversation = async (convId) => {
  const conv = conversations.value.find(c => c.id === convId)
  if (!conv || conv.messagesLoaded) return

  conv.isWaiting = true
  try {
    const { data, error } = await supabase
      .from('chat_history')
      .select('role, content, created_at')
      .eq('conversation_id', convId)
      .order('created_at', { ascending: true })
    
    if (error) throw error

    conv.messages = data.map((msg, idx) => ({
      id: msg.created_at + '_' + idx,
      role: msg.role,
      content: msg.content,
      attachments: [] // History won't re-download files for now
    }))
    conv.messagesLoaded = true
  } catch (err) {
    console.error('Failed to load chat history:', err)
  } finally {
    conv.isWaiting = false
  }
}

const selectConversation = async (id) => { 
  activeId.value = id
  if (currentUser.value) {
    await loadHistoryForConversation(id)
  }
}

const newConversation = () => {
  const conv = createConversation()
  conversations.value.unshift(conv)
  activeId.value = conv.id
}

const deleteConversation = async (id) => {
  const idx = conversations.value.findIndex(c => c.id === id)
  if (idx === -1) return

  // Optimistic UI update
  conversations.value.splice(idx, 1)
  
  if (conversations.value.length === 0) {
    newConversation()
  } else if (activeId.value === id) {
    activeId.value = conversations.value[Math.max(0, idx - 1)].id
  }

  // Delete from Supabase if logged in
  if (currentUser.value && id && !id.startsWith('temp_')) {
    await supabase.from('conversations').delete().eq('id', id)
  } else if (!currentUser.value && id) {
    // Free backend memory associated with guest session
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    fetch(`${baseUrl}/chat/session/${id}`, { method: 'DELETE' }).catch(err => console.error(err))
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
const autoListen = ref(true)         // auto-speak new assistant responses

const toggleAutoListen = () => { autoListen.value = !autoListen.value }

// ── Authentication ─────────────────────────────────────────────────────────
const showAuthModal = ref(false)
const currentUser = ref(null)
const profileDropdownOpen = ref(false)

const fetchConversations = async () => {
  if (!currentUser.value) {
    const guestData = sessionStorage.getItem('guest_conversations')
    if (guestData) {
      try {
        const parsed = JSON.parse(guestData)
        conversations.value = parsed.filter(c => c.messages && c.messages.length > 0)
      } catch (err) {
        console.error('Failed to parse guest conversations:', err)
      }
    }
    newConversation()
    return
  }
  
  try {
    const { data, error } = await supabase
      .from('conversations')
      .select('id, title, created_at')
      .order('created_at', { ascending: false })
      
    if (error) throw error

    if (data && data.length > 0) {
      conversations.value = data.map(row => ({
        id: row.id,
        threadId: row.id, // using DB ID as thread logic
        title: row.title,
        messages: [],
        messagesLoaded: false,
        isWaiting: false
      }))
      // Always start with a fresh blank canvas for the current user session
      newConversation()
    } else {
      newConversation()
    }
  } catch (err) {
    console.error('Failed to load conversations:', err)
    newConversation()
  }
}

onMounted(() => {
  // Check initial session
  supabase.auth.getSession().then(({ data }) => {
    currentUser.value = data.session?.user || null
    fetchConversations()
  })

  // Listen for auth changes
  supabase.auth.onAuthStateChange((_event, session) => {
    const prevUser = currentUser.value
    currentUser.value = session?.user || null
    
    if (currentUser.value && !prevUser) {
      // User just logged in
      fetchConversations()
    } else if (!currentUser.value && prevUser) {
      // User just logged out
      conversations.value = []
      sessionStorage.removeItem('guest_conversations')
      sessionStorage.removeItem('guest_active_id')
      newConversation()
    }
  })
})

// Persist guest state automatically
watch(conversations, () => {
  if (!currentUser.value) {
    sessionStorage.setItem('guest_conversations', JSON.stringify(conversations.value))
  }
}, { deep: true })

watch(activeId, () => {
  if (!currentUser.value && activeId.value) {
    sessionStorage.setItem('guest_active_id', activeId.value)
  }
})

const handleLogout = async () => {
  await supabase.auth.signOut()
  profileDropdownOpen.value = false
}

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
  
  let dbConvId = conv.id

  // 1. Create DB Conversation if New
  if (currentUser.value && (conv.title === 'New Chat' || !conv.id.includes('-'))) {
    const newTitle = payload.text ? (payload.text.slice(0, 36) + (payload.text.length > 36 ? '…' : '')) : 'New Chat'
    conv.title = newTitle

    const { data: convData, error: convErr } = await supabase
      .from('conversations')
      .insert({ title: newTitle, user_id: currentUser.value.id })
      .select()
      .single()
      
    if (!convErr && convData) {
      dbConvId = convData.id
      conv.id = dbConvId
      conv.threadId = dbConvId
      activeId.value = dbConvId
    }
  } else if (conv.title === 'New Chat' && payload.text) {
    conv.title = payload.text.slice(0, 36) + (payload.text.length > 36 ? '…' : '')
  }

  // 2. Add User Message to UI
  const userMsg = {
    id: Date.now(),
    role: 'user',
    content: payload.text || '📎 [File Attached]',
    attachments: payload.attachments || [],
  }
  conv.messages.push(userMsg)

  // 3. Insert User Message to DB
  if (currentUser.value) {
    await supabase.from('chat_history').insert({
      conversation_id: dbConvId,
      user_id: currentUser.value.id,
      role: 'user',
      content: userMsg.content
    })
  }

  conv.isWaiting = true

  // Create an AbortController so the request can be cancelled or timed out
  const controller = new AbortController()
  activeController.value = controller
  const timeoutId = setTimeout(() => controller.abort(), 90_000) // 90-second cap

  try {
    const backendUserId = currentUser.value ? currentUser.value.id : 'anonymous'
    
    let requestOptions = {}
    if (payload.attachments && payload.attachments.length > 0) {
      const formData = new FormData()
      formData.append('thread_id', conv.threadId)
      formData.append('user_id', backendUserId)
      formData.append('message', payload.text || 'Analyze attached files')
      payload.attachments.forEach(f => formData.append('files', f))
      requestOptions = { method: 'POST', body: formData, signal: controller.signal }
    } else {
      requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          thread_id: conv.threadId, 
          user_id: backendUserId, 
          message: payload.text || 'Process request' 
        }),
        signal: controller.signal,
      }
    }

    // Use environment variable for backend URL, fallback to localhost if missing
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const response = await fetch(`${baseUrl}/chat`, requestOptions)
    const data = await response.json()

    const target = conversations.value.find(c => c.id === dbConvId)
    if (target) {
      const assistantMsg = {
        id: Date.now() + 1,
        role: response.ok ? 'assistant' : 'system',
        content: response.ok ? data.response : `**Error:** ${data.error || 'Failed to reach API'}`,
      }
      target.messages.push(assistantMsg)

      // Insert Assistant Message to DB
      if (response.ok && currentUser.value) {
        await supabase.from('chat_history').insert({
          conversation_id: dbConvId,
          user_id: currentUser.value.id,
          role: 'assistant',
          content: assistantMsg.content
        })
      }
    }
  } catch (err) {
    const target = conversations.value.find(c => c.id === dbConvId)
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
    // Re-lookup by newly assigned DB DB to guarantee Vue reactivity
    const target = conversations.value.find(c => c.id === dbConvId)
    if (target) target.isWaiting = false
  }
}
</script>

<template>
  <div class="app-shell" @click="profileDropdownOpen = false">
    <ConversationSidebar
      :conversations="sortedConversations"
      :activeId="activeId"
      :autoListen="autoListen"
      @select="selectConversation"
      @new="newConversation"
      @delete="deleteConversation"
      @rename="renameConversation"
      @toggle-auto-listen="toggleAutoListen"
    />

    <div class="chat-pane">

      <!-- Top Header / Brand & Auth -->
      <header class="app-header">
        <div class="brand-main">TAR: The AI Researcher</div>
        
        <div class="auth-section">
          <template v-if="!currentUser">
            <button class="login-btn" @click="showAuthModal = true">Log In / Sign Up</button>
          </template>
          
          <template v-else>
            <div class="profile-menu-container" @click.stop>
              <button class="profile-btn" @click="profileDropdownOpen = !profileDropdownOpen" title="Profile Menu">
                <div class="avatar">{{ currentUser.user_metadata?.full_name?.charAt(0).toUpperCase() || currentUser.email.charAt(0).toUpperCase() }}</div>
              </button>
              
              <div v-if="profileDropdownOpen" class="profile-dropdown">
                <div class="dropdown-header">
                  <strong>{{ currentUser.user_metadata?.full_name || 'User' }}</strong>
                  <span class="user-email">{{ currentUser.email }}</span>
                </div>
                
                <div class="dropdown-meta">
                  <div class="meta-item">
                    <span class="meta-label">Org:</span>
                    <span class="meta-value">{{ currentUser.user_metadata?.organization || 'N/A' }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-label">Age:</span>
                    <span class="meta-value">{{ currentUser.user_metadata?.age || 'N/A' }}</span>
                  </div>
                </div>
                
                <button class="logout-btn" @click="handleLogout">Log Out</button>
              </div>
            </div>
          </template>
        </div>
      </header>

      <div class="guest-banner" v-if="!currentUser">
        💬 You are chatting as a guest. <a href="javascript:void(0)" @click="showAuthModal = true">Log in</a> to save your conversations permanently.
      </div>

      <!-- Scrollable body — messages OR centered empty state -->
      <div class="chat-body" id="chat-body">

        <div v-if="!hasMessages" class="empty-center">
          <div class="empty-hero">
            <div class="hero-glyph">✦</div>
            <h2>What do you want to explore?</h2>
            <p>Ask anything · Attach a PDF, image, or audio</p>
          </div>
        </div>

        <!-- Messages: scroll naturally from top -->
        <div v-else class="messages-zone">
          <ChatWindow
            :messages="activeConv?.messages || []"
            :isWaiting="activeConv?.isWaiting || false"
            :autoListen="autoListen"
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
    
    <!-- Auth Modal Overlay -->
    <AuthModal 
      v-if="showAuthModal" 
      @close="showAuthModal = false" 
      @auth-success="showAuthModal = false" 
    />
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
  padding: 2.5rem 2rem;
  background: rgba(240, 248, 255, 0.52);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  box-shadow: 0 8px 40px rgba(30, 50, 80, 0.1);
  max-width: 360px;
  width: 90%;
}

.hero-glyph {
  font-size: 2rem;
  margin-bottom: 0.85rem;
  color: #60809a;
  animation: glow 3s ease-in-out infinite;
}

.empty-hero h2 {
  margin: 0 0 0.4rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #202d3a;
  letter-spacing: -0.01em;
}

.empty-hero p {
  margin: 0;
  font-size: 0.8rem;
  color: #60809a;
}

@keyframes glow {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 1; }
}

.guest-banner {
  background-color: #fdf3cb8d;
  color: #856404;
  padding: 0.6rem 1rem;
  text-align: center;
  font-size: 0.85rem;
  border-bottom: 1px solid #ffeebac7;
  flex-shrink: 0;
}
.guest-banner a {
  color: #856404;
  font-weight: bold;
  text-decoration: underline;
  cursor: pointer;
}

/* ── Mobile Responsiveness ── */
@media (max-width: 768px) {
  .brand-main {
    padding-left: 3.5rem;
    font-size: 1rem;
  }
  .app-header {
    padding: max(1.2rem, env(safe-area-inset-top)) 1rem 0.5rem;
  }
  .empty-hero {
    padding: 1.5rem 1rem;
    max-width: 90%;
  }
  .messages-zone {
    padding: 3rem 0.5rem 1rem;
  }
  .input-bar {
    padding: 0.5rem 0.5rem max(0.5rem, env(safe-area-inset-bottom));
  }
  .footer-note {
    font-size: 0.6rem;
  }
}
</style>
