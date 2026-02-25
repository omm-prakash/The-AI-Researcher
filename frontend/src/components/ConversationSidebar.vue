<script setup>
import { ref } from 'vue'

const props = defineProps({
  conversations: Array,
  activeId: String,
})

const emit = defineEmits(['select', 'new', 'delete', 'rename'])

const collapsed = ref(false)
const editingId = ref(null)
const editingTitle = ref('')

const startRename = (conv) => {
  editingId.value = conv.id
  editingTitle.value = conv.title
}

const commitRename = (id) => {
  if (editingTitle.value.trim()) emit('rename', { id, title: editingTitle.value.trim() })
  editingId.value = null
}

const cancelRename = () => { editingId.value = null }
</script>

<template>
  <aside class="sidebar" :class="{ collapsed }">

    <!-- Hamburger / collapse toggle -->
    <button class="collapse-btn" @click="collapsed = !collapsed" :title="collapsed ? 'Expand' : 'Collapse'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <line x1="3" y1="8"  x2="21" y2="8"/>
        <line x1="3" y1="14" x2="21" y2="14"/>
      </svg>
    </button>

    <template v-if="!collapsed">

      <div class="sidebar-header">
        <span class="label">Chats</span>
        <button class="new-btn" @click="emit('new')" title="New conversation">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
      </div>

      <ul class="list">
        <li
          v-for="conv in conversations"
          :key="conv.id"
          :class="['item', { active: conv.id === activeId }]"
          @click="emit('select', conv.id)"
        >
          <template v-if="editingId === conv.id">
            <input
              class="rename-input"
              v-model="editingTitle"
              @blur="commitRename(conv.id)"
              @keydown.enter="commitRename(conv.id)"
              @keydown.escape="cancelRename"
              @click.stop
              autofocus
            />
          </template>
          <template v-else>
            <span class="item-title" @dblclick.stop="startRename(conv)">{{ conv.title }}</span>
            <button class="del-btn" @click.stop="emit('delete', conv.id)" title="Delete">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6"  x2="6"  y2="18"/>
                <line x1="6"  y1="6"  x2="18" y2="18"/>
              </svg>
            </button>
          </template>
        </li>
      </ul>

      <footer class="sidebar-footer">Double-click to rename</footer>
    </template>

  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;
  background: #0d0d10;
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  transition: width 0.22s ease, min-width 0.22s ease;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 48px;
  min-width: 48px;
}

.collapse-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #4a4a58;
  cursor: pointer;
  padding: 0.9rem;
  width: 100%;
  transition: color 0.18s, background 0.18s;
}
.collapse-btn:hover { color: #9898aa; background: rgba(255,255,255,0.025); }
.collapse-btn svg { width: 16px; height: 16px; }

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.8rem 0.9rem 0.5rem;
  flex-shrink: 0;
}

.label {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6868a0;
}

.new-btn {
  background: rgba(79, 110, 247, 0.15);
  border: 1px solid rgba(79, 110, 247, 0.25);
  color: #7a9bff;
  border-radius: 7px;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.18s, border-color 0.18s;
}
.new-btn:hover { background: rgba(79, 110, 247, 0.28); border-color: rgba(79,110,247,0.4); }
.new-btn svg { width: 13px; height: 13px; }

.list {
  list-style: none;
  margin: 0;
  padding: 0.2rem 0.5rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.65rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.14s;
  min-width: 0;
  border: 1px solid transparent;
}
.item:hover { background: rgba(255,255,255,0.035); }
.item.active {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.07);
}
.item:hover .del-btn { opacity: 1; }

.item-title {
  flex: 1;
  font-size: 0.82rem;
  font-weight: 400;
  color: #9898c0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  user-select: none;
  transition: color 0.14s;
}
.item.active .item-title { color: #e0e0f8; }
.item:hover .item-title  { color: #c0c0e0; }

.del-btn {
  opacity: 0;
  background: transparent;
  border: none;
  color: #44444e;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  transition: opacity 0.14s, color 0.14s;
}
.del-btn:hover { color: #d44; }
.del-btn svg { width: 12px; height: 12px; }

.rename-input {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(79,110,247,0.4);
  border-radius: 5px;
  color: #e0e0ee;
  font-size: 0.82rem;
  font-family: inherit;
  padding: 0.2rem 0.4rem;
  outline: none;
  min-width: 0;
}

.sidebar-footer {
  padding: 0.6rem 0.9rem;
  font-size: 0.64rem;
  color: #2e2e3a;
  flex-shrink: 0;
}
</style>
