<template>
  <div class="component-palette">
    <div class="palette-section">
      <h4 class="palette-title">指标类</h4>
      <div class="palette-grid">
        <div v-for="item in metricTypes" :key="item.type" class="palette-item" draggable="true" @dragstart="onDragStart($event, item)" @dragend="onDragEnd" @click="onPaletteClick(item)">
          <span class="palette-icon" v-html="item.icon"></span>
          <span class="palette-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <div class="palette-section">
      <h4 class="palette-title">折线 / 柱状</h4>
      <div class="palette-grid">
        <div v-for="item in axisTypes" :key="item.type" class="palette-item" draggable="true" @dragstart="onDragStart($event, item)" @dragend="onDragEnd" @click="onPaletteClick(item)">
          <span class="palette-icon" v-html="item.icon"></span>
          <span class="palette-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <div class="palette-section">
      <h4 class="palette-title">饼图 / 环形</h4>
      <div class="palette-grid">
        <div v-for="item in pieTypes" :key="item.type" class="palette-item" draggable="true" @dragstart="onDragStart($event, item)" @dragend="onDragEnd" @click="onPaletteClick(item)">
          <span class="palette-icon" v-html="item.icon"></span>
          <span class="palette-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <div class="palette-section">
      <h4 class="palette-title">表格类</h4>
      <div class="palette-grid">
        <div v-for="item in tableTypes" :key="item.type" class="palette-item" draggable="true" @dragstart="onDragStart($event, item)" @dragend="onDragEnd" @click="onPaletteClick(item)">
          <span class="palette-icon" v-html="item.icon"></span>
          <span class="palette-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <div class="palette-section">
      <h4 class="palette-title">其他组件</h4>
      <div class="palette-grid">
        <div v-for="item in otherTypes" :key="item.type" class="palette-item" draggable="true" @dragstart="onDragStart($event, item)" @dragend="onDragEnd" @click="onPaletteClick(item)">
          <span class="palette-icon" v-html="item.icon"></span>
          <span class="palette-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
    <a-divider />
    <div class="palette-section">
      <h4 class="palette-title">图层的管理</h4>
      <div class="layer-list">
        <div v-for="(panel, index) in panels" :key="panel.id" class="layer-item" :class="{ active: selectedPanelId === panel.id }" @click="$emit('select-panel', panel.id)">
          <span class="layer-index">{{ index + 1 }}</span>
          <span class="layer-icon" v-html="getLayerIcon(panel)"></span>
          <span class="layer-name">{{ panel.title || '未命名面板' }}</span>
          <a-button type="text" size="small" danger @click.stop="$emit('remove-panel', panel.id)"><template #icon><CloseOutlined /></template></a-button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { CloseOutlined } from '@ant-design/icons-vue'
import { chartTypeNames, getResolvedChartType } from './chartTypeRegistry.js'

const props = defineProps({
  panels: { type: Array, default: () => [] },
  selectedPanelId: { type: String, default: null },
})

const emit = defineEmits(['add-chart', 'select-panel', 'remove-panel'])

const isDragging = ref(false)

const iconSVG = {
  bar: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
  line: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
  pie: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>',
  doughnut: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path><circle cx="12" cy="12" r="3" fill="currentColor" fill-opacity="0.3"></circle></svg>',
  scatter: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="17" r="2"></circle><circle cx="16" cy="10" r="2"></circle><circle cx="20" cy="4" r="2"></circle><circle cx="5" cy="5" r="2"></circle></svg>',
  radar: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon><line x1="12" y1="2" x2="12" y2="22"></line><line x1="2" y1="8.5" x2="22" y2="15.5"></line><line x1="22" y1="8.5" x2="2" y2="15.5"></line></svg>',
  number_card: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
  table: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="3" x2="9" y2="21"></line></svg>',
  text: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>',
  heatmap: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect></svg>',
  funnel: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="3 3 21 3 14 14 14 21 10 21 10 14 3 3"></polygon></svg>',
  gauge: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"></path><path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"></path><line x1="12" y1="12" x2="12" y2="8"></line></svg>',
  image: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>',
  video: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>',
  iframe: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>',
  container: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="3" x2="9" y2="21"></line></svg>',
}

const metricTypes = [
  { type: 'number_card', icon: iconSVG.number_card, label: '数字卡片' },
  { type: 'gauge', icon: iconSVG.gauge, label: '仪表盘' },
]
const axisTypes = [
  { type: 'bar', icon: iconSVG.bar, label: '柱状图' },
  { type: 'line', icon: iconSVG.line, label: '折线图' },
  { type: 'scatter', icon: iconSVG.scatter, label: '散点图' },
]
const pieTypes = [
  { type: 'pie', icon: iconSVG.pie, label: '饼图' },
  { type: 'doughnut', icon: iconSVG.doughnut, label: '环形图' },
]
const tableTypes = [
  { type: 'table', icon: iconSVG.table, label: '数据表格' },
  { type: 'heatmap', icon: iconSVG.heatmap, label: '热力图' },
]
const otherTypes = [
  { type: 'radar', icon: iconSVG.radar, label: '雷达图' },
  { type: 'funnel', icon: iconSVG.funnel, label: '漏斗图' },
  { type: 'text', icon: iconSVG.text, label: '富文本' },
  { type: 'image', icon: iconSVG.image, label: '图片' },
  { type: 'video', icon: iconSVG.video, label: '视频' },
  { type: 'iframe', icon: iconSVG.iframe, label: '网页' },
  { type: 'container', icon: iconSVG.container, label: '容器/Tab' },
]

function getLayerIcon(panel) {
  const type = getResolvedChartType(panel, null)
  const svg = iconSVG[type] || iconSVG['bar']
  return svg.replace(/width="18"/g, 'width="14"').replace(/height="18"/g, 'height="14"')
}

function onDragStart(event, item) {
  isDragging.value = true
  event.dataTransfer.setData('chartType', item.type)
  event.dataTransfer.effectAllowed = 'copy'
}

function onDragEnd() {
  setTimeout(() => { isDragging.value = false }, 0)
}

function onPaletteClick(item) {
  if (isDragging.value) return
  emit('add-chart', item.type)
}
</script>

<style scoped>
.component-palette { padding: 12px; height: 100%; overflow-y: auto; }
.palette-section { margin-bottom: 12px; }
.palette-title { font-size: 11px; font-weight: 600; color: var(--color-text-tertiary); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.palette-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.palette-item { display: flex; flex-direction: column; align-items: center; padding: 10px 6px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); cursor: grab; transition: all 0.2s; background: var(--color-bg-surface); }
.palette-item:hover { border-color: var(--color-primary); background: var(--color-primary-light); box-shadow: var(--shadow-sm); }
.palette-item:active { cursor: grabbing; }
.palette-icon { display: flex; align-items: center; margin-bottom: 4px; color: var(--color-text-secondary); }
.palette-label { font-size: 11px; color: var(--color-text-secondary); }
.layer-list { display: flex; flex-direction: column; gap: 2px; }
.layer-item { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-radius: var(--radius-sm); cursor: pointer; transition: all 0.15s; border: 1px solid transparent; font-size: 13px; }
.layer-item:hover { background: var(--color-bg-page); }
.layer-item.active { background: var(--color-primary-light); border-color: var(--color-primary); }
.layer-index { font-size: 11px; color: var(--color-text-tertiary); width: 16px; text-align: center; }
.layer-icon { display: flex; align-items: center; color: var(--color-text-tertiary); }
.layer-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
