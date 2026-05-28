<template>
  <div v-show="visible" class="context-menu" :style="{ left: x + 'px', top: y + 'px' }">
    <div class="menu-item" @click="handleAction('copy')">复制 (Ctrl+C)</div>
    <div class="menu-item" @click="handleAction('paste')">粘贴 (Ctrl+V)</div>
    <div class="menu-item" @click="handleAction('delete')">删除 (Del)</div>
    <div class="menu-divider"></div>
    <div class="menu-item" @click="handleAction('top')">置于顶层</div>
    <div class="menu-item" @click="handleAction('bottom')">置于底层</div>
    <div class="menu-item" @click="handleAction('up')">上移一层</div>
    <div class="menu-item" @click="handleAction('down')">下移一层</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: Boolean,
  x: Number,
  y: Number
})

const emit = defineEmits(['action', 'update:visible'])

const handleAction = (action) => {
  emit('action', action)
  emit('update:visible', false)
}

const hideMenu = () => {
  emit('update:visible', false)
}

onMounted(() => {
  document.addEventListener('click', hideMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', hideMenu)
})
</script>

<style scoped>
.context-menu {
  position: absolute;
  background: var(--color-bg-elevated, #242D40);
  border: 1px solid var(--color-border, #2D3648);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
  padding: 4px 0;
  z-index: 9999;
  min-width: 150px;
  color: var(--color-text-primary);
  font-size: 13px;
}
.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.12s;
}
.menu-item:hover {
  background: var(--color-primary);
  color: #fff;
}
.menu-divider {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}
</style>
