<template>
  <div class="dashboard-view" :class="{ 'dark-theme': store.dashboard?.theme === 'dark' }">
    <div class="view-toolbar" v-if="!isFullscreen">
      <div class="toolbar-left">
        <a-button type="text" @click="goBack">
          <ArrowLeftOutlined /> 返回
        </a-button>
        <span class="view-title">{{ store.dashboard?.name || '数据大屏' }}</span>
      </div>
      <div class="toolbar-right">
        <a-space>
          <a-button @click="handleRefresh">
            <ReloadOutlined /> 刷新
          </a-button>
          <a-button @click="goToEdit">
            <EditOutlined /> 编辑
          </a-button>
          <a-button @click="toggleFullscreen">
            <FullscreenOutlined /> 全屏
          </a-button>
        </a-space>
      </div>
    </div>

    <div class="view-canvas" ref="canvasRef">
      <GridLayout
        v-if="store.dashboard"
        v-model:layout="layout"
        :col-num="12"
        :row-height="rowHeight"
        :is-draggable="false"
        :is-resizable="false"
        :margin="[12, 12]"
        :vertical-compact="true"
        :use-css-transforms="true"
      >
        <GridItem
          v-for="item in layout"
          :key="item.i"
          :x="item.x"
          :y="item.y"
          :w="item.w"
          :h="item.h"
          :i="item.i"
          static
        >
          <div class="view-panel">
            <ChartRenderer
              :chart-name="getPanelTitle(item.i)"
              :chart-type="getChartType(item.i)"
              :echarts-option="getChartOption(item.i)"
              :height="item.h * 100 - 12"
            />
          </div>
        </GridItem>
      </GridLayout>

      <a-empty
        v-if="store.panels.length === 0"
        description="暂无面板数据"
        style="margin-top: 120px"
      >
        <a-button type="primary" @click="goToEdit">去编辑</a-button>
      </a-empty>
    </div>

    <div class="view-refresh-indicator" v-if="autoRefresh">
      <a-tag color="processing">
        <SyncOutlined spin /> 自动刷新中 ({{ refreshInterval }}秒)
      </a-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GridLayout, GridItem } from 'vue-grid-layout-v3'
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  EditOutlined,
  FullscreenOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue'
import { useVizStore } from '../../stores/viz.js'
import ChartRenderer from '../../components/ChartRenderer.vue'

const route = useRoute()
const router = useRouter()
const store = useVizStore()

const canvasRef = ref(null)
const isFullscreen = ref(false)
let refreshTimer = null

const layout = computed(() => store.gridLayout)

const autoRefresh = computed(() => store.dashboard?.refresh_enabled || false)
const refreshInterval = computed(() => store.dashboard?.refresh_interval || 60)

const rowHeight = computed(() => {
  if (!canvasRef.value) return 100
  const height = canvasRef.value.clientHeight
  return Math.max(30, Math.floor((height - 12 * 11) / 6))
})

onMounted(async () => {
  const dashboardId = route.params.id
  if (dashboardId) {
    await store.loadDashboard(dashboardId)
  }
  if (autoRefresh.value) {
    startAutoRefresh()
  }
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  stopAutoRefresh()
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('keydown', onKeyDown)
})

function goBack() {
  router.push('/viz/dashboards')
}

function goToEdit() {
  if (store.dashboard) {
    router.push(`/viz/dashboards/${store.dashboard.id}/edit`)
  }
}

function handleRefresh() {
  store.loadDashboard(store.dashboard?.id)
}

function toggleFullscreen() {
  if (canvasRef.value) {
    canvasRef.value.requestFullscreen()
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

function onKeyDown(e) {
  if (e.key === 'Escape' && isFullscreen.value) {
    isFullscreen.value = false
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    handleRefresh()
  }, refreshInterval.value * 1000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

function getPanelTitle(panelId) {
  const panel = store.panels.find((p) => p.id === panelId)
  return panel?.title || '图表'
}

function getChartType(panelId) {
  return 'bar'
}

function getChartOption(panelId) {
  return {}
}
</script>

<style scoped>
.dashboard-view {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  font-family: var(--font-sans);
}

.dashboard-view.dark-theme {
  background: var(--color-sidebar-bg);
}

.view-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border-light);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.dark-theme .view-toolbar {
  background: var(--color-sidebar-hover);
  border-color: rgba(255, 255, 255, 0.06);
  color: var(--color-text-inverse);
}

.dark-theme .view-toolbar :deep(.ant-btn-text) {
  color: rgba(255, 255, 255, 0.7);
}

.dark-theme .view-toolbar :deep(.ant-btn-text:hover) {
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.08);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dark-theme .view-title {
  color: rgba(255, 255, 255, 0.75);
}

.view-canvas {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

.dark-theme .view-canvas {
  background: var(--color-sidebar-bg);
}

.view-panel {
  height: 100%;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.dark-theme .view-panel {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.dark-theme .view-panel :deep(.chart-renderer) {
  border-color: rgba(255, 255, 255, 0.06);
  background: transparent;
}

.dark-theme .view-panel :deep(.chart-header) {
  background: rgba(255, 255, 255, 0.03);
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .view-panel :deep(.chart-title) {
  color: rgba(255, 255, 255, 0.85);
}

.dark-theme .view-panel :deep(.chart-type-tag) {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}

.view-refresh-indicator {
  position: fixed;
  bottom: 24px;
  right: 24px;
}
</style>