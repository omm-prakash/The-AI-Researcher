<script setup>
import { ref } from 'vue'
import { supabase } from '../supabase'

const emit = defineEmits(['close', 'auth-success'])

const isLogin = ref(true)
const isLoading = ref(false)
const errorMessage = ref('')

// Form fields
const email = ref('')
const password = ref('')
const name = ref('')
const organization = ref('')
const age = ref('')

const toggleMode = () => {
  isLogin.value = !isLogin.value
  errorMessage.value = ''
  password.value = ''
}

const handleSubmit = async () => {
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    if (isLogin.value) {
      // ── LOGIN ──
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.value,
        password: password.value,
      })
      if (error) throw error
      emit('auth-success', data.user)
    } else {
      // ── SIGNUP ──
      if (!name.value || !organization.value || !age.value) {
        throw new Error('Please fill in all profile fields.')
      }
      
      const { data, error } = await supabase.auth.signUp({
        email: email.value,
        password: password.value,
        options: {
          data: {
            full_name: name.value,
            organization: organization.value,
            age: age.value
          }
        }
      })
      if (error) throw error
      
      // If email confirmation is enabled, user might not be logged in immediately
      if (data.session) {
        emit('auth-success', data.user)
      } else {
        errorMessage.value = 'Registration successful! Please check your email to verify your account.'
      }
    }
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <button class="close-btn" @click="emit('close')">✕</button>
      
      <h2>{{ isLogin ? 'Welcome Back' : 'Create an Account' }}</h2>
      <p class="subtitle">{{ isLogin ? 'Log in to continue your research.' : 'Join TAR for advanced AI research capabilities.' }}</p>
      
      <form @submit.prevent="handleSubmit" class="auth-form">
        
        <div class="input-group">
          <label>Email</label>
          <input type="email" v-model="email" required placeholder="name@example.com" :disabled="isLoading" />
        </div>
        
        <div class="input-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" :disabled="isLoading" minlength="6" />
        </div>

        <template v-if="!isLogin">
          <div class="input-group">
            <label>Full Name</label>
            <input type="text" v-model="name" required placeholder="Jane Doe" :disabled="isLoading" />
          </div>
          
          <div class="input-group">
            <label>Current Organization</label>
            <input type="text" v-model="organization" required placeholder="e.g. OpenAI, Stanford, Independent" :disabled="isLoading" />
          </div>
          
          <div class="input-group">
            <label>Age</label>
            <input type="number" v-model="age" required placeholder="25" min="13" max="120" :disabled="isLoading" />
          </div>
        </template>

        <div v-if="errorMessage" class="error-msg" :class="{ 'success-msg': errorMessage.includes('successful') }">
          {{ errorMessage }}
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading">
          {{ isLoading ? 'Processing...' : (isLogin ? 'Log In' : 'Sign Up') }}
        </button>
      </form>

      <div class="toggle-text">
        {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
        <a href="#" @click.prevent="toggleMode">{{ isLogin ? 'Sign Up' : 'Log In' }}</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(8, 12, 18, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-from, #ffffff);
  border: 1px solid var(--glass-border, #e2e8f0);
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
  padding: 2.2rem 2rem;
  position: relative;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  max-height: 90vh;
  overflow-y: auto;
}

/* Inherit dark mode text dynamically if active */
.modal-content h2 {
  margin: 0 0 0.5rem;
  color: var(--text-primary, #1a202c);
  font-size: 1.5rem;
  font-weight: 700;
}

.subtitle {
  color: var(--text-muted, #64748b);
  font-size: 0.85rem;
  margin-bottom: 1.8rem;
  line-height: 1.4;
}

.close-btn {
  position: absolute;
  top: 1.2rem; right: 1.2rem;
  background: transparent;
  border: none;
  font-size: 1.2rem;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  transition: color 0.2s;
}
.close-btn:hover { color: #ef4444; }

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.input-group label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-dim, #475569);
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-group input {
  width: 100%;
  padding: 0.75rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--glass-border-s, #cbd5e1);
  background: var(--glass-subtle, #f8fafc);
  color: var(--text-primary, #0f172a);
  font-size: 0.9rem;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}

.input-group input:focus {
  border-color: var(--accent, #3b82f6);
  box-shadow: 0 0 0 3px var(--accent-glow, rgba(59, 130, 246, 0.15));
}

.input-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-msg {
  color: #ef4444;
  font-size: 0.8rem;
  background: rgba(239, 68, 68, 0.1);
  padding: 0.6rem;
  border-radius: 6px;
  border: 1px solid rgba(239, 68, 68, 0.2);
  line-height: 1.4;
}

.success-msg {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.2);
}

.submit-btn {
  width: 100%;
  padding: 0.85rem;
  border: none;
  background: var(--accent, #3b82f6);
  color: white;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background 0.2s, transform 0.1s;
}
.submit-btn:hover:not(:disabled) {
  background: var(--accent-light, #2563eb);
}
.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.toggle-text {
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted, #64748b);
  margin-top: 1.5rem;
}

.toggle-text a {
  color: var(--accent, #3b82f6);
  font-weight: 600;
  text-decoration: none;
}
.toggle-text a:hover {
  text-decoration: underline;
}
</style>
