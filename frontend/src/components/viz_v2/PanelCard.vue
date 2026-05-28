<template>
  <div class="panel-card" :class="{ selected, dragging: isDragging }" @click.stop="$emit('select')" @dblclick.stop="$emit('edit')" @contextmenu.prevent="handleContextMenu">
    <div class="panel-header">
      <span class="panel-title">{{ panel.title || '未命名面板' }}</span>
      <a-dropdown :trigger="['click']">
        <a-button type="text" size="small" @click.stop>
          <MoreOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item key="edit" @click.stop="$emit('edit')"><EditOutlined /> 编辑配置</a-menu-item>
            <a-menu-item key="copy" @click.stop="$emit('copy')"><CopyOutlined /> 复制面板</a-menu-item>
            <a-menu-item key="hide" @click.stop="$emit('hide')"><EyeInvisibleOutlined /> 隐藏</a-menu-item>
            <a-menu-divider />
            <a-menu-item key="bringToFront" @click.stop="$emit('bringToFront')">置于顶层</a-menu-item>
            <a-menu-item key="sendToBack" @click.stop="$emit('sendToBack')">置于底层</a-menu-item>
            <a-menu-divider />
            <a-menu-item key="delete" danger @click.stop="$emit('delete')"><DeleteOutlined /> 删除面板</a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
    <div class="panel-body">
      <div v-if="hasChartContent" class="chart-content">
        <component :is="widgetComponent" :panel="panel" :chart-data="chartData" :is-dark-mode="isDarkMode" />
      </div>
      <div v-else class="empty-content">
        <span class="empty-icon" v-html="emptyIconSvg"></span>
        <span class="empty-text">双击编辑图表</span>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { MoreOutlined, EditOutlined, CopyOutlined, DeleteOutlined, EyeInvisibleOutlined } from '@ant-design/icons-vue'
import { getResolvedChartType } from './chartTypeRegistry.js'
import ChartWidget from './charts/ChartWidget.vue'
import NumberCardWidget from './charts/NumberCardWidget.vue'
import TableWidget from './charts/TableWidget.vue'
import TextWidget from './charts/TextWidget.vue'
import MediaWidget from './charts/MediaWidget.vue'
import ContainerWidget from './charts/ContainerWidget.vue'

const props = defineProps({
  panel: { type: Object, required: true },
  selected: { type: Boolean, default: false },
  chartData: { type: Object, default: null },
  isDarkMode: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'edit', 'copy', 'hide', 'delete', 'bringToFront', 'sendToBack', 'contextmenu'])
const isDragging = ref(false)

const chartTypeIcons = {
  bar: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
  line: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
  pie: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>',
  doughnut: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path><circle cx="12" cy="12" r="3"/></svg>',
  scatter: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="17" r="2"></circle><circle cx="16" cy="10" r="2"></circle><circle cx="20" cy="4" r="2"></circle><circle cx="5" cy="5" r="2"></circle></svg>',
  radar: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon><line x1="12" y1="2" x2="12" y2="22"></line><line x1="2" y1="8.5" x2="22" y2="15.5"></line><line x1="22" y1="8.5" x2="2" y2="15.5"></line></svg>',
  funnel: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="3 3 21 3 14 14 14 21 10 21 10 14 3 3"></polygon></svg>',
  gauge: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"></path><path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"></path><line x1="12" y1="12" x2="12" y2="8"></line></svg>',
  heatmap: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg>',
  table: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line></svg>',
  text: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>',
  number_card: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
  image: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>',
  video: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>',
  iframe: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>',
  container: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="3" x2="9" y2="21"></line></svg>',
}

const resolvedType = computed(() => {
  return getResolvedChartType(props.panel, props.chartData)
})

const emptyIconSvg = computed(() => {
  return chartTypeIcons[resolvedType.value] || chartTypeIcons['bar']
})

const hasChartContent = computed(() => {
  return !!(props.chartData && props.chartData.echarts_option && Object.keys(props.chartData.echarts_option).length > 0)
})

const echartsTypes = ['bar', 'line', 'pie', 'doughnut', 'scatter', 'radar', 'funnel', 'gauge', 'heatmap']

const widgetComponent = computed(() => {
  const type = resolvedType.value
  if (echartsTypes.includes(type)) return ChartWidget
  switch (type) {
    case 'number_card': return NumberCardWidget
    case 'table': return TableWidget
    case 'text': return TextWidget
    case 'image': case 'video': case 'iframe': return MediaWidget
    case 'container': return ContainerWidget
    default: return ChartWidget
  }
})

function handleContextMenu(e) {
  emit('contextmenu', { x: e.clientX, y: e.clientY, panelId: props.panel.id })
}
</script>
<style scoped>
.panel-card { height: 100%; width: 100%; border: 2px solid transparent; border-radius: var(--radius-md); background: var(--color-bg-surface); overflow: hidden; display: flex; flex-direction: column; transition: border-color 0.2s, box-shadow 0.2s; position: relative; }
.panel-card:hover { box-shadow: var(--shadow-md); }
.panel-card.selected { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(79,70,229,0.12); }
.panel-card.dragging { opacity: 0.6; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; border-bottom: 1px solid var(--color-border-light); flex-shrink: 0; }
.panel-title { font-size: 12px; font-weight: 600; color: var(--color-text-primary); }
.panel-body { flex: 1; overflow: hidden; min-height: 0; }
.chart-content { width: 100%; height: 100%; }
.empty-content { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--color-text-tertiary); gap: 6px; }
.empty-icon { display: flex; align-items: center; color: var(--color-text-tertiary); }
.empty-text { font-size: 12px; }
</style>
