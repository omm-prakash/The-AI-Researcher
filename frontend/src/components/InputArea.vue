<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: Boolean
})

const emit = defineEmits(['send'])

const text = ref('')
const textarea = ref(null)
const attachments = ref([])

const adjustHeight = () => {
  if (textarea.value) {
    textarea.value.style.height = 'auto';
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 200) + 'px';
  }
}

const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    attachments.value.push(...files);
    event.target.value = ''; // Reset input
}

const removeAttachment = (index) => {
    attachments.value.splice(index, 1);
}

const submit = () => {
  if ((!text.value.trim() && attachments.value.length === 0) || props.disabled) return
  
  emit('send', { text: text.value, attachments: [...attachments.value] })
  text.value = ''
  attachments.value = []
  if (textarea.value) {
    textarea.value.style.height = 'auto'
  }
}

const onKeyDown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

// Dummy record button state for UI completeness
const isRecording = ref(false)
const toggleRecord = () => {
    isRecording.value = !isRecording.value;
    if(!isRecording.value) {
        text.value += (text.value ? " " : "") + "[Audio Message Processing Component]";
    }
}
</script>

<template>
  <div class="input-wrapper" :class="{ disabled }">
    
    <div class="attachments-preview" v-if="attachments.length > 0">
        <div class="attachment-chip" v-for="(file, i) in attachments" :key="i">
            <span>{{ file.name }}</span>
            <button class="remove-btn" @click="removeAttachment(i)">×</button>
        </div>
    </div>
    
    <div class="input-box">
      <div class="actions-left">
        <label class="icon-btn" title="Attach file">
          <input type="file" multiple @change="handleFileSelect" style="display: none;" accept="image/*,.pdf" />
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
        </label>
      </div>
      
      <textarea
        ref="textarea"
        v-model="text"
        rows="1"
        placeholder="Message the assistant..."
        @input="adjustHeight"
        @keydown="onKeyDown"
        :disabled="disabled"
      ></textarea>
      
      <div class="actions-right">
        <button v-if="!text && attachments.length === 0" class="icon-btn mic-btn" :class="{ recording: isRecording }" @click="toggleRecord" title="Record Audio">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
        </button>
        
        <button v-else class="icon-btn send-btn" @click="submit" :disabled="disabled" title="Send Message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </div>
    <div class="footer-text">Assistant can make mistakes. Verify important information.</div>
  </div>
</template>

<style scoped>
.input-wrapper {
  position: relative;
  width: 100%;
}

.attachments-preview {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem 0;
    flex-wrap: wrap;
}

.attachment-chip {
    background: var(--bg-lighter);
    border: 1px solid var(--border);
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.remove-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1.1rem;
    line-height: 1;
}

.remove-btn:hover {
    color: #ef4444;
}

.input-box {
  display: flex;
  align-items: flex-end;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  padding: 0.5rem 1rem;
  box-shadow: var(--shadow);
  transition: border-color 0.2s;
}

.input-box:focus-within {
  border-color: rgba(255, 255, 255, 0.2);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  padding: 0.5rem 0.5rem;
  resize: none;
  max-height: 200px;
  overflow-y: auto;
  outline: none;
}

textarea::placeholder {
  color: var(--text-secondary);
}

.actions-left, .actions-right {
  display: flex;
  align-items: center;
  padding-bottom: 0.4rem;
}

.icon-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn svg {
  width: 20px;
  height: 20px;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.send-btn {
  color: white;
  background: var(--accent);
}

.send-btn:hover {
  background: var(--accent-hover);
}

.mic-btn.recording {
    color: #ef4444;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

.disabled {
  opacity: 0.7;
  pointer-events: none;
}

.footer-text {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 0.75rem;
}
</style>
