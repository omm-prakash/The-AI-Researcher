<script setup>
import { nextTick, watch, ref } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  messages: Array,
  isWaiting: Boolean,
})

const bottomAnchor = ref(null)

// Scroll to bottom whenever messages or waiting state changes
watch(
  [() => props.messages.length, () => props.isWaiting],
  async () => {
    await nextTick()
    bottomAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }
)

// ── Math rendering helpers (run BEFORE v-html, no DOM mutation) ───────────────

const renderMath = (html) => {
  // Block math: \[...\] and $$...$$
  html = html.replace(/\\\[([\s\S]+?)\\\]/g, (_, expr) => {
    try { return katex.renderToString(expr.trim(), { displayMode: true, throwOnError: false, strict: false }) }
    catch { return _ }
  })
  html = html.replace(/\$\$([\s\S]+?)\$\$/g, (_, expr) => {
    try { return katex.renderToString(expr.trim(), { displayMode: true, throwOnError: false, strict: false }) }
    catch { return _ }
  })
  // Inline math: \(...\) and $...$
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

const renderMarkdown = (content) => {
  const html = marked(content || '')
  return renderMath(html)
}
</script>

<template>
  <div class="messages">
    <div
      v-for="msg in messages"
      :key="msg.id"
      :class="['msg', msg.role]"
    >
      <div class="bubble markdown-body" v-html="renderMarkdown(msg.content)" />
      <div v-if="msg.attachments && msg.attachments.length" class="attach-row">
        <span v-for="(f, i) in msg.attachments" :key="i" class="attach-tag">📎 {{ f.name }}</span>
      </div>
    </div>

    <div v-if="isWaiting" class="msg assistant">
      <div class="bubble typing">
        <span /><span /><span />
      </div>
    </div>

    <!-- Invisible anchor — scrolled into view on each update -->
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
  background: #1e2030;
  border: 1px solid rgba(79, 110, 247, 0.2);
  border-bottom-right-radius: 4px;
  color: #ffffff;
}

.assistant .bubble {
  background: #131316;
  border: 1px solid rgba(255,255,255,0.06);
  border-bottom-left-radius: 4px;
  color: #f0f0f8;
}

.system .bubble {
  background: rgba(180, 50, 50, 0.08);
  border: 1px solid rgba(180,50,50,0.2);
  color: #c87070;
  border-radius: 10px;
}

.attach-row {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.4rem;
  flex-wrap: wrap;
}

.attach-tag {
  font-size: 0.72rem;
  color: #5a5a6e;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
}

/* Typing indicator */
.typing {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 1rem 1.25rem !important;
}
.typing span {
  width: 5px;
  height: 5px;
  background: #3a3a50;
  border-radius: 50%;
  animation: bounce 1.3s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.28s; }
.typing span:nth-child(2) { animation-delay: -0.14s; }

/* Markdown resets */
:deep(.markdown-body p)             { margin: 0 0 0.8em; }
:deep(.markdown-body p:last-child)  { margin-bottom: 0; }
:deep(.markdown-body ul),
:deep(.markdown-body ol)            { margin: 0.4em 0; padding-left: 1.4em; }
:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3)            { margin: 0.8em 0 0.4em; color: #ffffff; }
:deep(.markdown-body pre)           { background: rgba(0,0,0,0.45); padding: 0.9rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); overflow-x: auto; }
:deep(.markdown-body code)          { background: rgba(0,0,0,0.3); padding: 0.15rem 0.35rem; border-radius: 4px; font-size: 0.86em; color: #e8e8f8; }
:deep(.markdown-body a)             { color: #7a9bff; }
:deep(.markdown-body strong)        { color: #ffffff; }

/* KaTeX — ensure white text on dark background */
:deep(.katex)                       { color: #e8e8f8; font-size: 1em; }
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
</style>
