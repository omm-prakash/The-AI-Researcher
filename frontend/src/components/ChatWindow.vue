<script setup>
import { nextTick, watch, ref, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  messages: Array,
  isWaiting: Boolean,
  autoListen: { type: Boolean, default: true },
})

const emit = defineEmits(['reask'])

const bottomAnchor = ref(null)
const copiedId = ref(null)
const speakingId = ref(null)   // id of the message currently being spoken
const activeMsgId = ref(null)  // track which message is tapped on mobile to show actions

// Setup tap-outside to clear active message on mobile
const handleDocumentClick = (e) => {
  if (!e.target.closest('.msg')) {
    activeMsgId.value = null
  }
}

onMounted(() => {
  document.addEventListener('touchstart', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('touchstart', handleDocumentClick)
})

// Scroll to bottom & auto-speak when messages or waiting state changes
watch(
  () => [...props.messages], // Shallow copy to detect actual array pushes
  async (newMsgs, oldMsgs) => {
    await nextTick()
    bottomAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })

    const newLen = newMsgs.length
    const oldLen = oldMsgs ? oldMsgs.length : 0
    const added = newLen > oldLen

    // Auto-speak the newest assistant message if autoListen is on
    if (added && props.autoListen) {
      const last = newMsgs[newMsgs.length - 1]
      // Only speak if it's from the assistant AND it didn't just come from loading history
      if (last?.role === 'assistant') {
        speak(last)
      }
    }
  },
  { deep: true }
)

watch(
  () => props.isWaiting,
  async () => {
    await nextTick()
    bottomAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }
)

// ── Math rendering (runs before v-html, no DOM mutation) ─────────────────────

const renderMath = (html) => {
  html = html.replace(/\\\[([\s\S]+?)\\\]/g, (_, expr) => {
    try { return katex.renderToString(expr.trim(), { displayMode: true, throwOnError: false, strict: false }) }
    catch { return _ }
  })
  html = html.replace(/\$\$([\s\S]+?)\$\$/g, (_, expr) => {
    try { return katex.renderToString(expr.trim(), { displayMode: true, throwOnError: false, strict: false }) }
    catch { return _ }
  })
  html = html.replace(/\\\((.+?)\\\)/gs, (_, expr) => {
    try { return katex.renderToString(expr.trim(), { displayMode: false, throwOnError: false, strict: false }) }
    catch { return _ }
  })
  html = html.replace(/\$([^$\n]+?)\$/g, (_, expr) => {
    try { return katex.renderToString(expr.trim(), { displayMode: false, throwOnError: false, strict: false }) }
    catch { return _ }
  })
  return html
}

const renderMarkdown = (content) => renderMath(marked(content || ''))

const getFileIcon = (filename) => {
  if (!filename) return '📎'
  const lower = filename.toLowerCase()
  if (lower.match(/\.(jpg|jpeg|png|gif|webp)$/)) return '🖼️'
  if (lower.match(/\.(mp3|wav|ogg|m4a)$/)) return '🎵'
  if (lower.endsWith('.pdf')) return '📄'
  return '📎'
}

// ── Action handlers ────────────────────────────────────────────────────────

const copyContent = async (msg) => {
  try {
    await navigator.clipboard.writeText(msg.content)
  } catch {
    const el = document.createElement('textarea')
    el.value = msg.content
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
  copiedId.value = msg.id
  setTimeout(() => { copiedId.value = null; activeMsgId.value = null }, 2000)
}

const reask = (msg) => {
  emit('reask', msg.content)
  activeMsgId.value = null
}

// ── Text-to-speech ─────────────────────────────────────────────────────────

/** Strip HTML tags and markdown symbols so TTS reads clean prose. */
const plainText = (content) => {
  let text = (content || '')
    .replace(/<[^>]+>/g, ' ')               // html tags
    .replace(/```[\s\S]*?```/g, '')         // fenced code blocks
    .replace(/`[^`]+`/g, '')               // inline code
    .replace(/!?\[([^\]]+)\]\([^)]*\)/g, '$1') // links/images → label
    .replace(/[#*_~>|]+/g, ' ')             // md markers
    // strip emojis (covers most Unicode emoji ranges)
    .replace(/[\u{1F000}-\u{1FFFF}\u{2600}-\u{27FF}\u{FE00}-\u{FEFF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA9F}]/gu, '')
    .replace(/\s{2,}/g, ' ')               // collapse whitespace
    .trim()
  return text
}

const speak = (msg) => {
  if (!('speechSynthesis' in window)) return

  // Toggle: if this message is already playing, stop it
  if (speakingId.value === msg.id) {
    window.speechSynthesis.cancel()
    speakingId.value = null
    return
  }

  window.speechSynthesis.cancel()  // stop any previous

  const utterance = new SpeechSynthesisUtterance(plainText(msg.content))
  utterance.rate  = 1.0
  utterance.pitch = 1.0
  utterance.lang  = 'en-US'

  utterance.onstart = () => { speakingId.value = msg.id }
  utterance.onend   = () => { speakingId.value = null }
  utterance.onerror = () => { speakingId.value = null }

  window.speechSynthesis.speak(utterance)
}
</script>

<template>
  <div class="messages">
    <div
      v-for="msg in messages"
      :key="msg.id"
      :class="['msg', msg.role, { 'show-actions': activeMsgId === msg.id }]"
      @click="activeMsgId = msg.id"
    >
      <div class="bubble markdown-body" v-html="renderMarkdown(msg.content)" />

      <!-- Attachments row -->
      <div v-if="msg.attachments && msg.attachments.length" class="attach-row">
        <span v-for="(f, i) in msg.attachments" :key="i" class="attach-tag">{{ getFileIcon(f.name) }} {{ f.name }}</span>
      </div>

      <!-- Action buttons -->
      <div v-if="msg.role === 'user' || msg.role === 'assistant'" class="action-bar">
        <!-- Copy: available on both -->
        <button class="action-btn" @click="copyContent(msg)" :title="copiedId === msg.id ? 'Copied!' : 'Copy'">
          <template v-if="copiedId === msg.id">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Copied
          </template>
          <template v-else>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            Copy
          </template>
        </button>
        <!-- Re-ask: user messages only -->
        <button v-if="msg.role === 'user'" class="action-btn" @click="reask(msg)" title="Re-ask this question">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Re-ask
        </button>
        <!-- Listen: assistant messages only -->
        <button
          v-if="msg.role === 'assistant'"
          class="action-btn"
          :class="{ speaking: speakingId === msg.id }"
          @click="speak(msg)"
          :title="speakingId === msg.id ? 'Stop' : 'Listen'"
        >
          <!-- Stop icon when speaking -->
          <template v-if="speakingId === msg.id">
            <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
            Stop
          </template>
          <!-- Speaker icon when idle -->
          <template v-else>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
            </svg>
            Listen
          </template>
        </button>
      </div>
    </div>

    <!-- Typing indicator -->
    <div v-if="isWaiting" class="msg assistant">
      <div class="bubble typing">
        <span /><span /><span />
      </div>
    </div>

    <!-- Invisible scroll anchor -->
    <div ref="bottomAnchor" style="height:1px" />
  </div>
</template>

<style scoped>
.messages {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.msg {
  display: flex;
  flex-direction: column;
  max-width: 82%;
  animation: fadeUp 0.22s ease-out both;
}

.msg.user     { align-self: flex-end; }
.msg.assistant,
.msg.system   { align-self: flex-start; }

.bubble {
  padding: 0.85rem 1.1rem;
  border-radius: 14px;
  font-size: 0.9rem;
  line-height: 1.65;
}

.user .bubble {
  background: rgba(58, 171, 247, 0.613);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(130, 165, 200, 0.35);
  border-bottom-right-radius: 4px;
  color: #1a252c;
  box-shadow: 0 2px 12px rgba(30, 50, 100, 0.1);
}

.assistant .bubble {
  background: rgba(248, 249, 255, 0.719);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-bottom-left-radius: 4px;
  color: #1a252c;
  box-shadow: 0 2px 14px rgba(30, 50, 100, 0.08);
}

.system .bubble {
  background: rgba(210, 230, 255, 0.45);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(80, 130, 200, 0.3);
  color: #305ba0;
  border-radius: 10px;
}

/* ── Action bar ─────────────────────────────────────────────────────────── */
.action-bar {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.35rem;
  opacity: 0;
  transition: opacity 0.18s;
}

.msg:hover .action-bar { opacity: 1; }

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  background: rgba(240, 248, 255, 0.55);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(140, 175, 200, 0.35);
  color: #60809a;
  font-size: 0.72rem;
  font-family: inherit;
  padding: 0.25rem 0.65rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.action-btn svg { width: 12px; height: 12px; }

.action-btn:hover {
  color: #28455a;
  background: rgba(255, 255, 255, 0.75);
  border-color: rgba(100, 140, 180, 0.5);
}

.action-btn.speaking {
  color: #52778b;
  border-color: rgba(82, 119, 139, 0.45);
  background: rgba(82, 119, 139, 0.1);
  animation: pulse-tts 1.5s ease-in-out infinite;
}

@keyframes pulse-tts {
  0%, 100% { box-shadow: 0 0 0 0 rgba(82, 119, 139, 0); }
  50%       { box-shadow: 0 0 0 3px rgba(82, 119, 139, 0.18); }
}

/* ── Attachments ─────────────────────────────────────────────────────── */
.attach-row {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.4rem;
  flex-wrap: wrap;
}

.attach-tag {
  font-size: 0.72rem;
  color: #60809a;
  background: rgba(244, 248, 255, 0.7);
  border: 1px solid rgba(140, 175, 200, 0.3);
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
}

/* ── Typing indicator ─────────────────────────────────────────────── */
.typing {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 1rem 1.25rem !important;
}
.typing span {
  width: 5px;
  height: 5px;
  background: rgba(82, 119, 139, 0.45);
  border-radius: 50%;
  animation: bounce 1.3s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.28s; }
.typing span:nth-child(2) { animation-delay: -0.14s; }

/* ── Markdown ─────────────────────────────────────────────────────── */
:deep(.markdown-body p)             { margin: 0 0 0.8em; }
:deep(.markdown-body p:last-child)  { margin-bottom: 0; }
:deep(.markdown-body ul),
:deep(.markdown-body ol)            { margin: 0.4em 0; padding-left: 1.4em; }
:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3)            { margin: 0.8em 0 0.4em; color: #182a3a; }
:deep(.markdown-body pre)           { background: rgba(244, 248, 255, 0.75); backdrop-filter: blur(8px); padding: 0.9rem; border-radius: 8px; border: 1px solid rgba(140, 175, 200, 0.25); overflow-x: auto; }
:deep(.markdown-body code)          { background: rgba(232, 244, 255, 0.8); padding: 0.15rem 0.35rem; border-radius: 4px; font-size: 0.86em; color: #52778b; }
:deep(.markdown-body a)             { color: #52778b; }
:deep(.markdown-body strong)        { color: #182a3a; }

/* ── KaTeX ────────────────────────────────────────────────────────── */
:deep(.katex)                       { color: #1a252c; font-size: 1em; }
:deep(.katex-display)               { margin: 0.8em 0; overflow-x: auto; overflow-y: hidden; }
:deep(.katex-display > .katex)      { font-size: 1.1em; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.5); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ── Mobile Responsiveness ── */
@media (max-width: 768px) {
  .msg {
    max-width: 92%;
  }
  .bubble {
    padding: 0.75rem 0.9rem;
    font-size: 0.95rem; /* Keep at least 16px effective equivalent for readability and tap targets */
  }
  .action-bar {
    opacity: 0;
    transition: opacity 0.2s, max-height 0.2s;
    max-height: 0;
    overflow: hidden;
  }
  .msg.show-actions .action-bar {
    opacity: 1; /* Only show buttons on mobile if tapped */
    max-height: 40px;
  }
}
</style>

