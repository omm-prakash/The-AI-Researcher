<script setup>
import { ref } from 'vue'
import ChatWindow from './components/ChatWindow.vue'
import InputArea from './components/InputArea.vue'

const messages = ref([])
const isWaiting = ref(false)
const threadId = ref('thread_' + Math.random().toString(36).substr(2, 9))

const sendMessage = async (payload) => {
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: payload.text || '🎙️ [Audio Recorded] / 📎 [File Attached]',
    attachments: payload.attachments || []
  }
  
  messages.value.push(userMessage)
  isWaiting.value = true
  
  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        thread_id: threadId.value,
        message: payload.text || 'Process audio or attached files'
      })
    })
    
    const data = await response.json()
    if (response.ok) {
      messages.value.push({
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response
      })
    } else {
      messages.value.push({
        id: Date.now() + 1,
        role: 'system',
        content: `**Error:** ${data.error || 'Failed to reach API'}`
      })
    }
  } catch (err) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'system',
      content: `**Network Error:** Could not connect to API server. Ensure the Flask backend is running and CORS is enabled.\n\n${err.message}`
    })
  } finally {
    isWaiting.value = false
  }
}
</script>

<template>
  <div class="app-container">
    <div class="header">
      <h1>Agentic Research Assistant</h1>
    </div>
    
    <div class="chat-container" id="chat-container">
      <ChatWindow :messages="messages" :isWaiting="isWaiting" />
    </div>
    
    <div class="input-container">
      <InputArea @send="sendMessage" :disabled="isWaiting" />
    </div>
  </div>
</template>
