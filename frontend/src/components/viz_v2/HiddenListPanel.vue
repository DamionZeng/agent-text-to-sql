<template>
  <a-modal
    v-model:open="visible"
    title="隐藏组件列表"
    width="420px"
    @ok="visible = false"
  >
    <div class="hidden-list">
      <a-empty v-if="hiddenPanels.length === 0" description="暂无隐藏组件" />
      <div class="hidden-item" v-for="panel in hiddenPanels" :key="panel.id">
        <span class="hidden-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
        </span>
        <div class="hidden-info">
          <span class="hidden-name">{{ panel.title || '未命名组件' }}</span>
          <span class="hidden-type">{{ typeLabel(panel.chart_type) }}</span>
        </div>
        <a-button size="small" type="link" @click="handleRestore(panel.id)">恢复显示</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  hiddenPanels: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:open', 'restore'])

const visible = ref(false)

watch(() => props.open, (val) => { visible.value = val })
watch(visible, (val) => { emit('update:open', val) })

function typeLabel(type) {
  const map = { bar: '柱状图', line: '折线图', pie: '饼图', scatter: '散点图', radar: '雷达图', number_card: '数字卡片', table: '数据表格', text: '文本' }
  return map[type] || type || '图表'
}

function handleRestore(panelId) {
  emit('restore', panelId)
}
</script>

<style scoped>
.hidden-list { max-height: 350px; overflow-y: auto; }
.hidden-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border: 1px solid var(--color-border);
  border-radius: var(--radius-sm); margin-bottom: 8px;
  transition: all 0.15s;
}
.hidden-item:hover { border-color: var(--color-primary); }
.hidden-icon { display: flex; color: var(--color-text-tertiary); }
.hidden-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.hidden-name { font-size: 14px; font-weight: 500; }
.hidden-type { font-size: 12px; color: var(--color-text-tertiary); }
</style>
