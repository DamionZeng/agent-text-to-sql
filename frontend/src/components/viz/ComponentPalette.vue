<template>
  <div class="component-palette">
    <div class="palette-section">
      <h4 class="palette-title">图表组件</h4>
      <div class="palette-grid">
        <div
          v-for="item in chartTypes"
          :key="item.type"
          class="palette-item"
          draggable="true"
          @dragstart="onDragStart($event, item)"
        >
          <span class="palette-icon" v-html="item.icon"></span>
          <span class="palette-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <a-divider />
    <div class="palette-section">
      <h4 class="palette-title">图层管理</h4>
      <div class="layer-list">
        <div
          v-for="(panel, index) in panels"
          :key="panel.id"
          class="layer-item"
          :class="{ active: selectedPanelId === panel.id }"
          @click="$emit('select-panel', panel.id)"
        >
          <span class="layer-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
          </span>
          <span class="layer-name">{{ panel.title || '未命名面板' }}</span>
          <a-button
            type="text"
            size="small"
            danger
            @click.stop="$emit('remove-panel', panel.id)"
          >
            ×
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  panels: { type: Array, default: () => [] },
  selectedPanelId: { type: String, default: null },
})

defineEmits(['add-chart', 'select-panel', 'remove-panel'])

const chartTypes = [
  {
    type: 'bar',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    label: '柱状图'
  },
  {
    type: 'line',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
    label: '折线图'
  },
  {
    type: 'pie',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>',
    label: '饼图'
  },
  {
    type: 'scatter',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="17" r="2"></circle><circle cx="16" cy="10" r="2"></circle><circle cx="20" cy="4" r="2"></circle><circle cx="5" cy="5" r="2"></circle></svg>',
    label: '散点图'
  },
  {
    type: 'radar',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon><line x1="12" y1="2" x2="12" y2="22"></line><line x1="2" y1="8.5" x2="22" y2="15.5"></line><line x1="22" y1="8.5" x2="2" y2="15.5"></line></svg>',
    label: '雷达图'
  },
  {
    type: 'number_card',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
    label: '数字卡'
  },
  {
    type: 'table',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line></svg>',
    label: '数据表'
  },
  {
    type: 'text',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>',
    label: '文本'
  },
]

function onDragStart(event, item) {
  event.dataTransfer.setData('chartType', item.type)
  event.dataTransfer.effectAllowed = 'copy'
}
</script>

<style scoped>
.component-palette {
  padding: 12px;
  height: 100%;
  overflow-y: auto;
}

.palette-section {
  margin-bottom: 8px;
}

.palette-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.palette-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.palette-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: grab;
  transition: all 0.2s;
  background: var(--color-bg-surface);
}

.palette-item:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  box-shadow: var(--shadow-sm);
}

.palette-item:active {
  cursor: grabbing;
}

.palette-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  color: var(--color-text-secondary);
}

.palette-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.layer-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.layer-item:hover {
  background: var(--color-bg-page);
}

.layer-item.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

.layer-icon {
  display: flex;
  align-items: center;
  color: var(--color-text-tertiary);
}

.layer-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>