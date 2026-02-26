<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'

const props = defineProps({ disabled: Boolean, prefill: String })
const emit = defineEmits(['send', 'clear-prefill'])

const text = ref('')
const textarea = ref(null)
const attachments = ref([])
const dragging = ref(false)

// When parent sets a prefill value (from Re-ask), populate the textarea and focus it
watch(() => props.prefill, async (val) => {
  if (val) {
    text.value = val
    emit('clear-prefill')
    await nextTick()
    adjustHeight()
    textarea.value?.focus()
    const len = text.value.length
    textarea.value?.setSelectionRange(len, len)
  }
})

const adjustHeight = () => {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 180) + 'px'
  }
}

// Accepted file extensions
const ACCEPTED_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp3', '.wav', '.ogg', '.m4a', '.pdf']

const getFileIcon = (filename) => {
  if (!filename) return '📎'
  const lower = filename.toLowerCase()
  if (lower.match(/\.(jpg|jpeg|png|gif|webp)$/)) return '🖼️'
  if (lower.match(/\.(mp3|wav|ogg|m4a)$/)) return '🎵'
  if (lower.endsWith('.pdf')) return '📄'
  return '📎'
}

const addFile = (file) => {
  if (!file) return
  const name = file.name.toLowerCase()
  if (!ACCEPTED_EXTS.some(ext => name.endsWith(ext))) return
  attachments.value = [file]   // one file at a time
}

// ── File picker ────────────────────────────────────────────────────────────
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) addFile(files[files.length - 1])
  event.target.value = ''
}

// ── Paste from clipboard (images via Ctrl+V / Cmd+V) ──────────────────────
const onPaste = (event) => {
  const items = Array.from(event.clipboardData?.items || [])
  const fileItem = items.find(i => i.kind === 'file' && (
    i.type.startsWith('image/') || i.type === 'application/pdf' || i.type.startsWith('audio/')
  ))
  if (fileItem) {
    event.preventDefault()       // don't paste as text
    addFile(fileItem.getAsFile())
  }
}

// ── Drag and drop ──────────────────────────────────────────────────────────
const onDragOver = (event) => {
  event.preventDefault()
  dragging.value = true
}
const onDragLeave = () => { dragging.value = false }
const onDrop = (event) => {
  event.preventDefault()
  dragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length > 0) addFile(files[0])
}

// ── Misc ───────────────────────────────────────────────────────────────────
const removeAttachment = (i) => attachments.value.splice(i, 1)

const submit = () => {
  if ((!text.value.trim() && attachments.value.length === 0) || props.disabled) return
  stopMic()   // turn off mic before sending
  emit('send', { text: text.value, attachments: [...attachments.value] })
  text.value = ''
  committedText = ''
  attachments.value = []
  if (textarea.value) textarea.value.style.height = 'auto'
}

const onKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
}

// ── Voice input (Web Speech API) ────────────────────────────────────────────

const isListening   = ref(false)
const micSupported  = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window

let recognition     = null
let committedText   = ''   // text before the current interim segment

const buildRecognition = () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  const r  = new SR()
  r.lang            = 'en-US'
  r.continuous      = true   // keep listening until explicitly stopped
  r.interimResults  = true   // fire events for partial results in real-time

  r.onstart = () => {
    isListening.value = true
    committedText     = text.value  // snapshot current textarea content
  }

  r.onresult = (event) => {
    let interim = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        committedText += (committedText && !committedText.endsWith(' ') ? ' ' : '') + t
      } else {
        interim = t
      }
    }
    // Show committed + live interim in the textarea
    text.value = committedText + (interim ? (committedText && !committedText.endsWith(' ') ? ' ' : '') + interim : '')
    nextTick(() => {
      adjustHeight()
      textarea.value?.focus()   // keep focus so Enter key sends immediately
    })
  }

  r.onerror = (e) => {
    if (e.error !== 'aborted') console.warn('[Mic] SpeechRecognition error:', e.error)
    isListening.value = false
  }

  r.onend = () => {
    isListening.value = false
  }

  return r
}

const startMic = () => {
  if (!micSupported) return
  // Pause/stop any ongoing Text-to-Speech when the user starts the mic
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel()
  }
  recognition = buildRecognition()
  recognition.start()
}

const stopMic = () => {
  recognition?.stop()
  isListening.value = false
}

const toggleMic = () => {
  if (isListening.value) stopMic()
  else startMic()
}

// Clean up on unmount
onBeforeUnmount(() => stopMic())
</script>

<template>
  <div
    class="input-wrap"
    :class="{ disabled, dragging }"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >

    <!-- Attachment chips -->
    <div class="chips" v-if="attachments.length">
      <div class="chip" v-for="(file, i) in attachments" :key="i">
        <span>{{ getFileIcon(file.name) }} {{ file.name }}</span>
        <button class="chip-rm" @click="removeAttachment(i)">×</button>
      </div>
    </div>

    <!-- Drag-over overlay hint -->
    <div v-if="dragging" class="drop-hint">Drop file here</div>

    <div class="box">
      <!-- Left: attach -->
      <label class="icon-btn" title="Attach file">
        <input type="file" @change="handleFileSelect" style="display:none" accept=".jpg,.jpeg,.png,.gif,.webp,.mp3,.wav,.ogg,.m4a,.pdf" />
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
        </svg>
      </label>

      <textarea
        ref="textarea"
        v-model="text"
        rows="1"
        placeholder="Message the assistant…"
        @input="adjustHeight"
        @keydown="onKeyDown"
        @paste="onPaste"
        :disabled="disabled"
      />

      <!-- Mic button — always visible when no text, hidden if unsupported -->
      <button
        v-if="!text && micSupported"
        class="icon-btn mic-btn"
        :class="{ recording: isListening }"
        @click="toggleMic"
        :title="isListening ? 'Stop recording' : 'Speak your message'"
        :disabled="disabled"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8"  y1="23" x2="16" y2="23"/>
        </svg>
      </button>

      <!-- Send button -->
      <button
        v-if="text || attachments.length"
        class="icon-btn send-btn"
        @click="submit"
        :disabled="disabled"
        title="Send"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-wrap {
  width: 100%;
  position: relative;
}

/* Drag-over ring */
.input-wrap.dragging .box {
  border-color: rgba(82, 119, 139, 0.65);
  box-shadow:
    0 0 0 3px rgba(82, 119, 139, 0.18),
    0 0 24px rgba(82, 119, 139, 0.12);
}

/* Drop hint */
.drop-hint {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.8rem;
  color: #354d5a;
  pointer-events: none;
  white-space: nowrap;
  z-index: 2;
}

.chips {
  display: flex;
  gap: 0.4rem;
  padding: 0.4rem 0 0.5rem;
  flex-wrap: wrap;
}

.chip {
  background: rgba(191, 212, 248, 0.75);
  border: 1px solid rgba(130, 165, 200, 0.3);
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  font-size: 0.78rem;
  color: #40627a;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.chip-rm {
  background: none;
  border: none;
  color: #303f4a;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  transition: color 0.15s;
}
.chip-rm:hover { color: #c04040; }

.box {
  display: flex;
  align-items: flex-end;
  background: rgba(240, 248, 255, 0.62);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 14px;
  padding: 0.45rem 0.8rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  gap: 0.25rem;
  box-shadow: 0 4px 20px rgba(30, 50, 100, 0.08);
}

.box:focus-within {
  border-color: rgba(100, 140, 180, 0.6);
  box-shadow:
    0 0 0 3px rgba(82, 119, 139, 0.12),
    0 4px 24px rgba(30, 50, 100, 0.12);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #1a252c;
  font-family: inherit;
  font-size: 0.93rem;
  line-height: 1.55;
  padding: 0.35rem 0.5rem;
  resize: none;
  max-height: 180px;
  overflow-y: auto;
  outline: none;
}

textarea::placeholder { color: #495f76; }

.icon-btn {
  background: transparent;
  border: none;
  color: #586777;
  cursor: pointer;
  padding: 0.4rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.18s, background 0.18s;
  flex-shrink: 0;
}
.icon-btn svg { width: 18px; height: 18px; }
.icon-btn:hover { color: #3a5462; background: rgba(82, 119, 139, 0.08); }

.send-btn { color: #3b5664; }
.send-btn:hover {
  color: #30516a;
  background: rgba(82, 119, 139, 0.12);
}

.mic-btn { color: #445968; }
.mic-btn:hover {
  color: #c04040;
  background: rgba(192, 64, 64, 0.07);
}

.mic-btn.recording {
  color: #c04040;
  background: rgba(192, 64, 64, 0.09);
  border-radius: 8px;
  animation: mic-pulse 1.4s ease-in-out infinite;
}

@keyframes mic-pulse {
  0%, 100% { box-shadow: 0 0 0 0   rgba(192, 64, 64, 0);    }
  50%       { box-shadow: 0 0 0 4px rgba(192, 64, 64, 0.22); }
}

.disabled { opacity: 0.5; pointer-events: none; }

/* ── Mobile Responsiveness ── */
@media (max-width: 768px) {
  .box {
    padding: 0.35rem 0.5rem;
  }
  textarea {
    font-size: 16px; /* 16px prevents automatic zoom on iOS Safari */
    padding: 0.25rem 0.4rem;
  }
  .icon-btn {
    padding: 0.35rem;
  }
}
</style>

