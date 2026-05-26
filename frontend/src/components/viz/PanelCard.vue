<template>
  <div
    class="panel-card"
    :class="{ selected: selected, dragging: isDragging }"
    @click.stop="$emit('select')"
  >
    <div class="panel-header">
      <span class="panel-title">{{ panel.title || '未命名面板' }}</span>
      <a-dropdown :trigger="['click']">
        <a-button type="text" size="small" @click.stop>
          <MoreOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item key="edit" @click.stop="$emit('edit')">
              <EditOutlined /> 编辑配置
            </a-menu-item>
            <a-menu-item key="copy" @click.stop="$emit('copy')">
              <CopyOutlined /> 复制面板
            </a-menu-item>
            <a-menu-divider />
            <a-menu-item key="delete" danger @click.stop="$emit('delete')">
              <DeleteOutlined /> 删除面板
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
    <div class="panel-body">
      <div v-if="chartData" class="chart-content">
        <ChartRenderer
          :chart-name="panel.title || '图表'"
          :chart-type="chartData.chart_type || 'bar'"
          :echarts-option="chartData.echarts_option || {}"
          :height="panelHeight - 40"
          :show-header="false"
        />
      </div>
      <div v-else class="empty-content">
        <span class="empty-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
          </svg>
        </span>
        <span class="empty-text">选择图表配置</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MoreOutlined, EditOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import ChartRenderer from '../ChartRenderer.vue'

const props = defineProps({
  panel: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  chartData: { type: Object, default: null },
})

defineEmits(['select', 'edit', 'copy', 'delete'])

const isDragging = ref(false)

const panelHeight = computed(() => {
  return (props.panel.layout_h || 4) * 104
})
</script>

<style scoped>
.panel-card {
  height: 100%;
  width: 100%;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  background: var(--color-bg-surface);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.panel-card:hover {
  box-shadow: var(--shadow-md);
}

.panel-card.selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.12);
}

.panel-card.dragging {
  opacity: 0.6;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-body {
  flex: 1;
  overflow: hidden;
}

.chart-content {
  width: 100%;
  height: 100%;
}

.empty-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  gap: 8px;
}

.empty-icon {
  display: flex;
  align-items: center;
  color: var(--color-text-tertiary);
}

.empty-text {
  font-size: 13px;
}
</style>