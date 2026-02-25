<script setup>
import { ref } from 'vue'

const props = defineProps({ disabled: Boolean })
const emit = defineEmits(['send'])

const text = ref('')
const textarea = ref(null)
const attachments = ref([])

const adjustHeight = () => {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 180) + 'px'
  }
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) attachments.value = [files[files.length - 1]]
  event.target.value = ''
}

const removeAttachment = (i) => attachments.value.splice(i, 1)

const submit = () => {
  if ((!text.value.trim() && attachments.value.length === 0) || props.disabled) return
  emit('send', { text: text.value, attachments: [...attachments.value] })
  text.value = ''
  attachments.value = []
  if (textarea.value) textarea.value.style.height = 'auto'
}

const onKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
}
</script>

<template>
  <div class="input-wrap" :class="{ disabled }">

    <!-- Attachment chips -->
    <div class="chips" v-if="attachments.length">
      <div class="chip" v-for="(file, i) in attachments" :key="i">
        <span>{{ file.name }}</span>
        <button class="chip-rm" @click="removeAttachment(i)">×</button>
      </div>
    </div>

    <div class="box">
      <!-- Left: attach -->
      <label class="icon-btn" title="Attach file">
        <input type="file" @change="handleFileSelect" style="display:none" accept="image/*,.pdf,audio/*" />
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
        :disabled="disabled"
      />

      <!-- Right: send or mic -->
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
      <button v-else class="icon-btn" title="Voice (coming soon)" disabled>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8"  y1="23" x2="16" y2="23"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-wrap {
  width: 100%;
}

.chips {
  display: flex;
  gap: 0.4rem;
  padding: 0.4rem 0 0.5rem;
  flex-wrap: wrap;
}

.chip {
  background: #1a1a20;
  border: 1px solid rgba(255,255,255,0.08);
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  font-size: 0.78rem;
  color: #888898;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.chip-rm {
  background: none;
  border: none;
  color: #555566;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  transition: color 0.15s;
}
.chip-rm:hover { color: #d44; }

.box {
  display: flex;
  align-items: flex-end;
  background: #111116;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 0.45rem 0.8rem;
  transition: border-color 0.2s;
  gap: 0.25rem;
}

.box:focus-within {
  border-color: rgba(255,255,255,0.15);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #d8d8e8;
  font-family: inherit;
  font-size: 0.93rem;
  line-height: 1.55;
  padding: 0.35rem 0.5rem;
  resize: none;
  max-height: 180px;
  overflow-y: auto;
  outline: none;
}

textarea::placeholder { color: #3a3a4a; }

.icon-btn {
  background: transparent;
  border: none;
  color: #3a3a4a;
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
.icon-btn:hover { color: #8888a0; background: rgba(255,255,255,0.04); }

.send-btn {
  color: #4f6ef7;
}
.send-btn:hover {
  color: #7a9bff;
  background: rgba(79, 110, 247, 0.1);
}

.disabled { opacity: 0.5; pointer-events: none; }
</style>
