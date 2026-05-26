<template>
  <div class="dashboard-editor" :class="{ 'dark-theme': store.dashboard?.theme === 'dark' }">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <a-button type="text" @click="goBack">
          <ArrowLeftOutlined /> 返回列表
        </a-button>
        <div class="name-display" v-if="!isEditingName" @click="startEditName">
          <span class="name-text">{{ editorName || '未命名大屏' }}</span>
          <EditOutlined class="name-edit-icon" />
        </div>
        <a-input
          v-else
          ref="nameInputRef"
          v-model:value="editorName"
          class="name-input"
          placeholder="大屏名称"
          bordered="false"
          @blur="finishEditName"
          @keydown.enter="finishEditName"
        />
      </div>
      <div class="toolbar-right">
        <a-space>
          <a-button @click="handleSave">
            <SaveOutlined /> 保存
          </a-button>
          <a-button @click="goToView">
            <EyeOutlined /> 预览
          </a-button>
          <a-button type="primary" @click="handlePublish" v-if="store.dashboard?.status !== 'published'">
            <SendOutlined /> 发布
          </a-button>
        </a-space>
      </div>
    </div>

    <div class="editor-body" v-if="!aiGenerating">
      <!-- Left Mini Dock (collapsed state) -->
      <div
        class="left-mini-dock"
        :class="{ 'docked-expanded': leftDockExpanded }"
        @mouseenter="leftDockHovered = true"
        @mouseleave="leftDockHovered = false"
        v-if="leftSidebarCollapsed"
      >
        <div class="mini-dock-icon" @click="toggleLeftSidebar" title="展开组件面板">
          <AppstoreOutlined />
        </div>
        <div class="mini-dock-divider"></div>
        <div class="mini-dock-icon" @click="handleDockSelectPanel" title="选择图表">
          <BorderOutlined />
        </div>
        <div class="mini-dock-icon" @click="goToView" title="预览">
          <EyeOutlined />
        </div>
        <div class="mini-dock-divider"></div>
        <div class="mini-dock-bottom">
          <div class="mini-dock-icon" @click="showRightPanelViaDock" title="显示配置">
            <SettingOutlined />
          </div>
          <div class="mini-dock-icon expand-btn" @click="toggleLeftSidebar" title="展开面板">
            <RightOutlined />
          </div>
        </div>
      </div>

      <!-- Left Sidebar (full) -->
      <div
        class="left-sidebar-panel"
        :class="{ 'left-hidden': leftSidebarCollapsed }"
      >
        <div class="left-sidebar-inner">
          <ComponentPalette
            :panels="store.panels"
            :selected-panel-id="store.selectedPanelId"
            @select-panel="handleLeftPanelSelect"
            @remove-panel="handleRemovePanel"
          />
        </div>
        <!-- Bottom toggle arrows -->
        <div class="sidebar-bottom-toggle">
          <div class="bottom-toggle-btn" @click="toggleLeftSidebar">
            <LeftOutlined v-if="!leftSidebarCollapsed" />
            <RightOutlined v-else />
          </div>
        </div>
      </div>

      <!-- Canvas -->
      <div class="editor-canvas-wrapper">
        <GlobalFilterBar
          :filters="store.filters"
          @filter-change="handleFilterChange"
        />

        <div
          class="editor-canvas"
          @drop.prevent="onDrop"
          @dragover.prevent
        >
          <GridLayout
            v-if="store.dashboard"
            v-model:layout="layout"
            :col-num="12"
            :row-height="100"
            :is-draggable="true"
            :is-resizable="true"
            :margin="[12, 12]"
            :vertical-compact="true"
            :use-css-transforms="true"
            @layout-updated="onLayoutUpdated"
          >
            <GridItem
              v-for="item in layout"
              :key="item.i"
              :x="item.x"
              :y="item.y"
              :w="item.w"
              :h="item.h"
              :i="item.i"
            >
              <PanelCard
                :panel="getPanel(item.i)"
                :selected="store.selectedPanelId === item.i"
                :chart-data="getChartData(item.i)"
                @select="handleCanvasPanelClick(item.i)"
                @edit="onEditPanel(item.i)"
                @delete="handleRemovePanel(item.i)"
              />
            </GridItem>
          </GridLayout>

          <a-empty
            v-if="store.panels.length === 0"
            description="拖拽左侧图表组件到此处，或从图表列表添加"
            style="margin-top: 80px"
          />
        </div>
      </div>

      <!-- Right Floating Config Panel -->
      <Transition name="right-panel">
        <div
          class="right-float-panel"
          v-if="store.selectedPanel && rightPanelVisible"
        >
          <div class="right-panel-header">
            <span class="right-panel-title">{{ store.selectedPanel.title || '图表配置' }}</span>
            <a-button type="text" size="small" class="right-panel-close" @click="closeRightPanel">
              <CloseOutlined />
            </a-button>
          </div>
          <div class="right-panel-body">
            <PanelConfigPanel
              :panel="store.selectedPanel"
              :chart-data="getChartData(store.selectedPanelId)"
              :dashboard="store.dashboard"
              @apply="handleApplyConfig"
              @execute-sql="handleExecuteSql"
            />
          </div>
        </div>
      </Transition>
    </div>

    <div class="ai-progress-overlay" v-if="aiGenerating">
      <div class="ai-progress-card">
        <h3 class="ai-progress-title">
          <LoadingOutlined spin style="margin-right: 8px" />
          AI 正在生成大屏...
        </h3>

        <div class="ai-flow">
          <template v-for="(stg, idx) in stages" :key="stg.id">
            <div
              class="flow-stage"
              :class="'stage-' + stg.status"
              @click="toggleStage(idx)"
            >
              <div class="flow-stage-icon">
                <LoadingOutlined spin v-if="stg.status === 'running'" />
                <span class="icon-check" v-else-if="stg.status === 'success'">&#10003;</span>
                <span class="icon-error" v-else-if="stg.status === 'error'">&#10007;</span>
                <span class="icon-pending" v-else>{{ idx + 1 }}</span>
              </div>
              <div class="flow-stage-label">{{ stg.label }}</div>
              <div class="flow-stage-info" v-if="stg.count">
                {{ stg.count }}个面板
              </div>
            </div>
            <div class="flow-arrow" v-if="idx < stages.length - 1">
              <span>&#10132;</span>
            </div>
          </template>
        </div>

        <div class="ai-detail-panel" v-if="expandedStage">
          <div class="detail-header">
            <span class="detail-title">{{ expandedStage.label }} 详情</span>
            <span
              class="detail-collapse"
              @click="expandedStage = null"
            >收起</span>
          </div>
          <div class="detail-steps">
            <div
              v-for="(sub, si) in expandedStage.subSteps"
              :key="si"
              class="detail-step-item"
              :class="'step-' + sub.status"
            >
              <span class="detail-step-icon">
                <LoadingOutlined spin v-if="sub.status === 'running'" />
                <span class="icon-check" v-else-if="sub.status === 'success'">&#10003;</span>
                <span class="icon-error" v-else-if="sub.status === 'error'">&#10007;</span>
                <span class="icon-pending" v-else>&#9679;</span>
              </span>
              <span class="detail-step-text">{{ sub.name || sub.message }}</span>
            </div>
          </div>
        </div>

        <div class="ai-progress-error" v-if="aiError">
          <a-alert :message="aiError" type="error" show-icon />
          <a-button type="primary" style="margin-top: 12px" @click="goBack">返回列表</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GridLayout, GridItem } from 'vue-grid-layout-v3'
import {
  ArrowLeftOutlined,
  SaveOutlined,
  EyeOutlined,
  SendOutlined,
  EditOutlined,
  LoadingOutlined,
  LeftOutlined,
  RightOutlined,
  AppstoreOutlined,
  BorderOutlined,
  MenuOutlined,
  CloseOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { useVizStore } from '../../stores/viz.js'
import ComponentPalette from '../../components/viz/ComponentPalette.vue'
import PanelCard from '../../components/viz/PanelCard.vue'
import PanelConfigPanel from '../../components/viz/PanelConfigPanel.vue'
import GlobalFilterBar from '../../components/viz/GlobalFilterBar.vue'

const route = useRoute()
const router = useRouter()
const store = useVizStore()

const editorName = ref('')
const isEditingName = ref(false)
const nameInputRef = ref(null)
const chartDataCache = ref({})
const leftSidebarCollapsed = ref(false)
const rightSidebarCollapsed = ref(false)
const rightPanelVisible = ref(true)
const leftDockHovered = ref(false)
const leftDockExpanded = ref(false)
const leftSidebarPanelHovered = ref(false)

function syncChartDataCache() {
  for (const panel of store.panels) {
    if (panel.chart_config_id && !chartDataCache.value[panel.id]) {
      chartDataCache.value[panel.id] = {
        chart_type: panel.chart_type || 'bar',
        sql_text: panel.sql_text || '',
        echarts_option: panel.echarts_option || {},
      }
    }
  }
}

const aiGenerating = ref(false)
const aiError = ref('')

const stageDefs = [
  { id: 'parse_intent', label: '解析需求' },
  { id: 'generate_sqls', label: '生成SQL' },
  { id: 'generate_charts', label: '生成图表' },
  { id: 'plan_layout', label: '规划布局' },
  { id: 'assemble_dashboard', label: '组装大屏' },
]

function createStages() {
  return stageDefs.map((d) => ({
    ...d,
    status: 'pending',
    subSteps: [],
    count: 0,
  }))
}

const stages = ref(createStages())
const expandedStage = ref(null)

function findStage(stepId) {
  return stages.value.find((s) => s.id === stepId)
}

function toggleStage(idx) {
  if (expandedStage.value === stages.value[idx]) {
    expandedStage.value = null
  } else {
    expandedStage.value = stages.value[idx]
  }
}

const layout = computed({
  get: () => store.gridLayout,
  set: (val) => { /* handled by layout-updated */ },
})

onMounted(async () => {
  const dashboardId = route.params.id
  const isAi = route.query.ai === 'true'
  const prompt = route.query.prompt
  const datasourceId = route.query.datasourceId

  if (isAi && prompt && datasourceId) {
    await handleAiGenerate(datasourceId, prompt)
  } else if (dashboardId && dashboardId !== 'new') {
    const data = await store.loadDashboard(dashboardId)
    if (data) {
      editorName.value = data.dashboard?.name || ''
    }
    syncChartDataCache()
  }
})
async function handleAiGenerate(datasourceId, prompt) {
  aiGenerating.value = true
  aiError.value = ''
  stages.value = createStages()

  try {
    const res = await fetch('/api/viz/dashboards/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ datasource_id: datasourceId, prompt }),
    })

    if (!res.ok) {
      throw new Error(`请求失败: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let dashboardId = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue

        try {
          const data = JSON.parse(trimmed.slice(6))

          if (data.type === 'progress') {
            const stg = findStage(data.step)
            if (stg) {
              stg.status = data.status
              if (data.panel_index !== undefined) {
                const existing = stg.subSteps.find(
                  (s) => s.index === data.panel_index
                )
                if (existing) {
                  existing.status = data.status
                  existing.message = data.message || ''
                } else {
                  stg.subSteps.push({
                    index: data.panel_index,
                    name: data.panel_name || `面板${data.panel_index + 1}`,
                    message: data.message || '',
                    status: data.status,
                  })
                }
              }
              if (data.status === 'success') {
                let count = 0
                if (data.message && data.message.includes('个面板')) {
                  const m = data.message.match(/(\d+)\s*个面板/)
                  if (m) count = parseInt(m[1])
                } else {
                  count = stg.subSteps.length
                }
                if (count) stg.count = count
              }
              if (data.status === 'running' && !expandedStage.value) {
                expandedStage.value = stg
              }
            }
          } else if (data.type === 'dashboard_result') {
            dashboardId = data.dashboard_id
            editorName.value = data.dashboard_name || prompt.slice(0, 50)
          } else if (data.type === 'error') {
            aiError.value = data.message || '生成失败'
          }
        } catch (parseErr) {
          console.warn('SSE 解析失败:', parseErr, trimmed)
        }
      }
    }

    if (dashboardId) {
      router.replace({
        path: `/viz/dashboards/${dashboardId}/edit`,
        query: {},
      })
      await store.loadDashboard(dashboardId)
      if (store.dashboard) {
        editorName.value = store.dashboard.name || editorName.value
      }
      syncChartDataCache()
    } else if (!aiError.value) {
      aiError.value = '未能生成大屏，请重试'
    }
  } catch (e) {
    console.error('AI 生成大屏失败:', e)
    aiError.value = e.message || '生成失败'
  } finally {
    aiGenerating.value = false
  }
}

function getPanel(id) {
  return store.panels.find((p) => p.id === id) || {}
}

function getChartData(panelId) {
  return chartDataCache.value[panelId] || null
}

function goBack() {
  router.push('/viz/dashboards')
}

function toggleLeftSidebar() {
  leftSidebarCollapsed.value = !leftSidebarCollapsed.value
  leftDockExpanded.value = false
}

function closeRightPanel() {
  rightSidebarCollapsed.value = true
  rightPanelVisible.value = false
}

function showRightPanel() {
  rightSidebarCollapsed.value = false
  rightPanelVisible.value = true
}

async function handleLeftPanelSelect(panelId) {
  store.selectPanel(panelId)
  showRightPanel()
  await nextTick()
  if (!rightPanelVisible.value && store.selectedPanel) {
    rightPanelVisible.value = true
    rightSidebarCollapsed.value = false
  }
}

async function handleCanvasPanelClick(panelId) {
  store.selectPanel(panelId)
  showRightPanel()
  await nextTick()
  if (!rightPanelVisible.value && store.selectedPanel) {
    rightPanelVisible.value = true
    rightSidebarCollapsed.value = false
  }
}

function handleDockSelectPanel() {
  const firstPanel = store.panels[0]
  if (firstPanel) {
    store.selectPanel(firstPanel.id)
    showRightPanel()
  }
}

function showRightPanelViaDock() {
  if (store.selectedPanel) {
    showRightPanel()
  } else {
    handleDockSelectPanel()
  }
}

function startEditName() {
  isEditingName.value = true
  nextTick(() => {
    if (nameInputRef.value) {
      nameInputRef.value.focus()
    }
  })
}

function finishEditName() {
  isEditingName.value = false
}

function goToView() {
  if (store.dashboard) {
    router.push(`/viz/dashboards/${store.dashboard.id}/view`)
  }
}

async function handleSave() {
  try {
    if (editorName.value) {
      await store.saveDashboard({ name: editorName.value })
    }
    await store.updateLayout(layout.value)
  } catch (e) {
    console.error('保存失败', e)
  }
}

async function handlePublish() {
  try {
    await store.saveDashboard({ status: 'published' })
  } catch (e) {
    console.error('发布失败', e)
  }
}

async function handleRemovePanel(panelId) {
  try {
    await store.removePanel(store.dashboard.id, panelId)
  } catch (e) {
    console.error('删除面板失败', e)
  }
}

function onLayoutUpdated(newLayout) {
  store.updateLayout(newLayout)
}

function onEditPanel(panelId) {
  store.selectPanel(panelId)
}

async function handleApplyConfig(formData) {
  if (!store.selectedPanel) return
  const panel = store.selectedPanel
  try {
    await store.updatePanelConfig(store.selectedPanelId, {
      title: formData.title,
      layout_x: formData.layout_x,
      layout_y: formData.layout_y,
      layout_w: formData.layout_w,
      layout_h: formData.layout_h,
      sort_order: formData.sort_order,
    })
    if (panel.chart_config_id) {
      await store.updateChartConfig(panel.chart_config_id, {
        chart_type: formData.chartType,
        sql_text: formData.sql_text,
      })
      chartDataCache.value[store.selectedPanelId] = {
        chart_type: formData.chartType || 'bar',
        sql_text: formData.sql_text || '',
        echarts_option: chartDataCache.value[store.selectedPanelId]?.echarts_option || {},
      }
    }
  } catch (e) {
    console.error('应用配置失败', e)
  }
}

function handleExecuteSql() {
  console.log('执行SQL')
}

function handleFilterChange(filterEvent) {
  console.log('筛选器变化', filterEvent)
}

function onDrop(event) {
  const chartType = event.dataTransfer.getData('chartType')
  if (chartType && store.dashboard) {
    store.addPanel(store.dashboard.id, null, `新建${chartType}图表`, {
      x: 0,
      y: 0,
      w: 6,
      h: 4,
    })
  }
}
</script>

<style scoped>
.dashboard-editor {
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

.dashboard-editor.dark-theme {
  background: var(--color-sidebar-bg);
  color: var(--color-text-inverse);
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.dark-theme .editor-toolbar {
  background: var(--color-sidebar-hover);
  border-color: rgba(255, 255, 255, 0.06);
  color: var(--color-text-inverse);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dark-theme .toolbar-left :deep(.ant-btn-text) {
  color: rgba(255, 255, 255, 0.6);
}

.dark-theme .toolbar-left :deep(.ant-btn-text:hover) {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.08);
}

.name-display {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.name-display:hover {
  background: rgba(0, 0, 0, 0.04);
}

.dark-theme .name-display:hover {
  background: rgba(255, 255, 255, 0.06);
}

.name-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dark-theme .name-text {
  color: rgba(255, 255, 255, 0.75);
}

.name-edit-icon {
  font-size: 13px;
  color: var(--color-text-tertiary);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.name-display:hover .name-edit-icon {
  opacity: 1;
}

.dark-theme .name-edit-icon {
  color: rgba(255, 255, 255, 0.35);
}

.dark-theme .name-display:hover .name-edit-icon {
  color: rgba(255, 255, 255, 0.6);
}

.name-input {
  width: 300px;
  font-size: 16px;
  font-weight: 600;
  font-family: var(--font-sans);
}

.dark-theme .name-input :deep(input) {
  color: rgba(255, 255, 255, 0.85);
}

.dark-theme .name-input :deep(input::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* ======= Left Mini Dock (collapsed state) ======= */
.left-mini-dock {
  position: relative;
  width: 0;
  flex-shrink: 0;
  background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border-light);
  overflow: hidden;
  transition: width 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 8px;
  gap: 4px;
  z-index: 20;
}

.left-mini-dock:hover,
.left-mini-dock.docked-expanded {
  width: 48px;
}

.mini-dock-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-size: 16px;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.mini-dock-icon:hover {
  background: rgba(79, 70, 229, 0.1);
  color: var(--color-primary);
}

.mini-dock-divider {
  width: 24px;
  height: 1px;
  background: var(--color-border-light);
  margin: 4px 0;
  flex-shrink: 0;
}

.mini-dock-spacer {
  flex: 1;
}

.mini-dock-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding-bottom: 8px;
  border-top: 1px solid var(--color-border-light);
  margin-top: auto;
  width: 100%;
  padding-top: 8px;
}

.mini-dock-icon.expand-btn {
  color: var(--color-primary);
  background: rgba(79, 70, 229, 0.08);
}

.mini-dock-icon.expand-btn:hover {
  background: rgba(79, 70, 229, 0.18);
  color: var(--color-primary);
}

/* ======= Left Full Sidebar Panel ======= */
.left-sidebar-panel {
  width: 240px;
  flex-shrink: 0;
  background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border-light);
  overflow: hidden;
  transition: width 0.25s ease, opacity 0.25s ease;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
}

.left-sidebar-panel.left-hidden {
  width: 0;
  opacity: 0;
}

.left-sidebar-inner {
  width: 240px;
  flex: 1;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-bottom-toggle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
  border-top: 1px solid var(--color-border-light);
  background: inherit;
  z-index: 11;
}

.bottom-toggle-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-size: 12px;
  transition: background 0.15s, color 0.15s;
}

.bottom-toggle-btn:hover {
  background: rgba(79, 70, 229, 0.1);
  color: var(--color-primary);
}

/* ======= Right Floating Panel ======= */
.right-float-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 340px;
  background: var(--color-bg-surface);
  border-left: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  z-index: 50;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.06);
  overflow: visible;
}

.right-panel-enter-active,
.right-panel-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.right-panel-enter-from,
.right-panel-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.right-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
  min-width: 0;
  overflow: visible;
}

.right-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.right-panel-close {
  color: var(--color-text-secondary) !important;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background 0.15s, color 0.15s;
  font-size: 14px;
}

.right-panel-close:hover {
  background: rgba(79, 70, 229, 0.1) !important;
  color: var(--color-primary) !important;
}

.right-panel-body {
  flex: 1;
  overflow-y: auto;
}

/* ======= Dark Theme ======= */
.dark-theme .left-mini-dock {
  background: var(--color-sidebar-hover);
  border-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .mini-dock-divider {
  background: rgba(255, 255, 255, 0.08);
}

.dark-theme .left-sidebar-panel {
  background: var(--color-sidebar-hover);
  border-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .left-sidebar-panel.left-hidden {
  border-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .right-float-panel {
  background: var(--color-sidebar-hover);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.3);
}

.dark-theme .right-panel-header {
  border-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .right-panel-title {
  color: rgba(255, 255, 255, 0.9);
}

.dark-theme .bottom-toggle-btn {
  color: rgba(255, 255, 255, 0.5);
}

.dark-theme .bottom-toggle-btn:hover {
  background: rgba(79, 70, 229, 0.15);
  color: #818cf8;
}

.dark-theme :deep(.palette-title) {
  color: rgba(255, 255, 255, 0.5);
}

.dark-theme :deep(.palette-item) {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
}

.dark-theme :deep(.palette-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--color-primary);
}

.dark-theme :deep(.palette-label) {
  color: rgba(255, 255, 255, 0.7);
}

.dark-theme :deep(.palette-icon) {
  color: rgba(255, 255, 255, 0.6);
}

.dark-theme :deep(.layer-item) {
  color: rgba(255, 255, 255, 0.65);
}

.dark-theme :deep(.layer-item:hover) {
  background: rgba(255, 255, 255, 0.06);
}

.dark-theme :deep(.ant-tabs-nav) {
  margin-bottom: 8px;
}

.dark-theme :deep(.ant-tabs-tab) {
  color: rgba(255, 255, 255, 0.5);
  padding: 6px 12px;
}

.dark-theme :deep(.ant-tabs-tab-active) {
  color: rgba(255, 255, 255, 0.9);
}

.dark-theme :deep(.ant-tabs-ink-bar) {
  background: var(--color-primary);
}

.dark-theme :deep(.ant-tabs-nav::before) {
  border-color: rgba(255, 255, 255, 0.06);
}

.dark-theme :deep(.ant-form-item-label > label) {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.dark-theme :deep(.ant-input),
.dark-theme :deep(.ant-input-number),
.dark-theme :deep(.ant-select-selector),
.dark-theme :deep(.ant-input-number-input) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.85);
}

.dark-theme :deep(.ant-input:focus),
.dark-theme :deep(.ant-input-number-focused),
.dark-theme :deep(.ant-select-focused .ant-select-selector) {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

.dark-theme :deep(.ant-input::placeholder),
.dark-theme :deep(.ant-select-selection-placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.dark-theme :deep(.ant-select-arrow) {
  color: rgba(255, 255, 255, 0.4);
}

.dark-theme :deep(.sql-editor) {
  background: rgba(255, 255, 255, 0.04);
}

.dark-theme :deep(.layer-item.active) {
  background: rgba(79, 70, 229, 0.15);
  border-color: var(--color-primary);
  color: rgba(255, 255, 255, 0.9);
}

.dark-theme :deep(.layer-icon) {
  color: rgba(255, 255, 255, 0.5);
}

.dark-theme :deep(.layer-name) {
  color: rgba(255, 255, 255, 0.75);
}

/* Right panel dark theme */
.dark-theme .right-float-panel :deep(.ant-tabs-nav) {
  margin-bottom: 8px;
}

.dark-theme .right-float-panel :deep(.ant-tabs-tab) {
  color: rgba(255, 255, 255, 0.5);
  padding: 6px 12px;
}

.dark-theme .right-float-panel :deep(.ant-tabs-tab-active) {
  color: rgba(255, 255, 255, 0.9);
}

.dark-theme .right-float-panel :deep(.ant-tabs-ink-bar) {
  background: var(--color-primary);
}

.dark-theme .right-float-panel :deep(.ant-tabs-nav::before) {
  border-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .right-float-panel :deep(.ant-form-item-label > label) {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.dark-theme .right-float-panel :deep(.ant-input),
.dark-theme .right-float-panel :deep(.ant-input-number),
.dark-theme .right-float-panel :deep(.ant-select-selector),
.dark-theme .right-float-panel :deep(.ant-input-number-input) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.85);
}

.dark-theme .right-float-panel :deep(.ant-input:focus),
.dark-theme .right-float-panel :deep(.ant-input-number-focused),
.dark-theme .right-float-panel :deep(.ant-select-focused .ant-select-selector) {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

.dark-theme .right-float-panel :deep(.ant-input::placeholder),
.dark-theme .right-float-panel :deep(.ant-select-selection-placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.dark-theme .right-float-panel :deep(.ant-select-arrow) {
  color: rgba(255, 255, 255, 0.4);
}

.dark-theme .right-float-panel :deep(.config-footer) {
  border-top-color: rgba(255, 255, 255, 0.08);
}

.dark-theme .right-float-panel :deep(.sql-editor) {
  background: rgba(255, 255, 255, 0.04);
}

.editor-canvas-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.dark-theme .editor-canvas-wrapper {
  background: var(--color-sidebar-bg);
}

.editor-canvas {
  flex: 1;
  padding: 16px;
  min-height: 600px;
}

.dark-theme .editor-canvas-wrapper :deep(.global-filter-bar) {
  background: rgba(255, 255, 255, 0.03);
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .editor-canvas-wrapper :deep(.filter-label) {
  color: rgba(255, 255, 255, 0.6);
}

.dark-theme .editor-canvas-wrapper :deep(.panel-card) {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.dark-theme .editor-canvas-wrapper :deep(.panel-header) {
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .editor-canvas-wrapper :deep(.panel-title) {
  color: rgba(255, 255, 255, 0.85);
}

.dark-theme .editor-canvas-wrapper :deep(.empty-text) {
  color: rgba(255, 255, 255, 0.4);
}

.dark-theme .editor-canvas-wrapper :deep(.empty-icon) {
  color: rgba(255, 255, 255, 0.35);
}

.dark-theme .editor-canvas-wrapper :deep(.chart-renderer) {
  border-color: rgba(255, 255, 255, 0.08);
  background: transparent;
}

.dark-theme .editor-canvas-wrapper :deep(.chart-header) {
  background: rgba(255, 255, 255, 0.04);
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

.dark-theme .editor-canvas-wrapper :deep(.chart-title) {
  color: rgba(255, 255, 255, 0.85);
}

.dark-theme .editor-canvas-wrapper :deep(.chart-type-tag) {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}

.ai-progress-overlay {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
}

.dark-theme .ai-progress-overlay {
  background: var(--color-sidebar-bg);
}

.ai-progress-card {
  background: var(--color-bg-surface);
  border-radius: 12px;
  padding: 32px 40px;
  min-width: 560px;
  max-width: 700px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.dark-theme .ai-progress-card {
  background: var(--color-sidebar-hover);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.ai-progress-title {
  margin: 0 0 28px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
}

.dark-theme .ai-progress-title {
  color: rgba(255, 255, 255, 0.9);
}

/* ========== Flow Diagram ========== */
.ai-flow {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.flow-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  min-width: 80px;
  border: 2px solid transparent;
  background: rgba(0, 0, 0, 0.02);
}

.dark-theme .flow-stage {
  background: rgba(255, 255, 255, 0.03);
}

.flow-stage:hover {
  background: rgba(79, 70, 229, 0.06);
  border-color: rgba(79, 70, 229, 0.3);
}

.dark-theme .flow-stage:hover {
  background: rgba(129, 140, 248, 0.08);
  border-color: rgba(129, 140, 248, 0.3);
}

.flow-stage.stage-running {
  background: rgba(79, 70, 229, 0.08);
  border-color: var(--color-primary);
  box-shadow: 0 0 12px rgba(79, 70, 229, 0.2);
}

.dark-theme .flow-stage.stage-running {
  background: rgba(129, 140, 248, 0.12);
  border-color: #818cf8;
  box-shadow: 0 0 16px rgba(129, 140, 248, 0.25);
}

.flow-stage.stage-success {
  background: rgba(82, 196, 26, 0.04);
  border-color: rgba(82, 196, 26, 0.2);
}

.flow-stage.stage-error {
  background: rgba(255, 77, 79, 0.06);
  border-color: rgba(255, 77, 79, 0.3);
}

.flow-stage-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.06);
  color: var(--color-text-tertiary);
  transition: all 0.25s ease;
}

.dark-theme .flow-stage-icon {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.35);
}

.stage-running .flow-stage-icon {
  background: var(--color-primary);
  color: #fff;
}

.stage-success .flow-stage-icon {
  background: #52c41a;
  color: #fff;
}

.stage-error .flow-stage-icon {
  background: #ff4d4f;
  color: #fff;
}

.icon-check { color: #fff; }
.icon-error { color: #fff; }
.icon-pending { color: inherit; }

.flow-stage-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.stage-running .flow-stage-label {
  color: var(--color-primary);
  font-weight: 600;
}

.stage-success .flow-stage-label {
  color: #52c41a;
}

.flow-stage-info {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.flow-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  font-size: 18px;
  color: var(--color-text-tertiary);
  margin-top: 10px;
}

.dark-theme .flow-arrow {
  color: rgba(255, 255, 255, 0.25);
}

/* ========== Detail Panel ========== */
.ai-detail-panel {
  margin-top: 4px;
  margin-bottom: 20px;
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  overflow: hidden;
}

.dark-theme .ai-detail-panel {
  border-color: rgba(255, 255, 255, 0.08);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid var(--color-border-light);
}

.dark-theme .detail-header {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.06);
}

.detail-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dark-theme .detail-title {
  color: rgba(255, 255, 255, 0.85);
}

.detail-collapse {
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
}

.detail-collapse:hover {
  text-decoration: underline;
}

.detail-steps {
  padding: 8px 14px;
  max-height: 200px;
  overflow-y: auto;
}

.detail-step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.detail-step-item.step-running {
  color: var(--color-primary);
}

.detail-step-item.step-success {
  color: #52c41a;
}

.detail-step-item.step-error {
  color: #ff4d4f;
}

.detail-step-icon {
  font-size: 12px;
  width: 18px;
  text-align: center;
}

.detail-step-text {
  flex: 1;
}

.ai-progress-error {
  margin-top: 16px;
}
</style>