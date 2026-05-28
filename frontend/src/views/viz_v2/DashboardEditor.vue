<template>
  <div class="dashboard-editor" :class="{ 'dark-theme': store.dashboard?.theme === 'dark' }">
    <!-- ========== DbToolbar: Full Toolbar ========== -->
    <div class="editor-toolbar">
      <!-- Left Section -->
      <div class="tb-left">
        <a-button type="text" class="tb-btn" @click="goBack" title="返回列表">
          <ArrowLeftOutlined />
        </a-button>
        <div class="tb-divider"></div>
        <div class="name-display" v-if="!isEditingName" @dblclick="startEditName">
          <span class="name-text">{{ editorName || '未命名仪表板' }}</span>
          <EditOutlined class="name-edit-icon" />
        </div>
        <a-input v-else ref="nameInputRef" v-model:value="editorName" class="name-input" placeholder="仪表板名称" bordered="false" @blur="finishEditName" @keydown.enter="finishEditName" />
        <div class="tb-divider"></div>
        <a-button type="text" class="tb-btn" :disabled="!canUndo" @click="handleUndo" title="撤销 (Undo)">
          <UndoOutlined />
        </a-button>
        <a-button type="text" class="tb-btn" :disabled="!canRedo" @click="handleRedo" title="重做 (Redo)">
          <RedoOutlined />
        </a-button>
      </div>

      <!-- Middle Section: Component Buttons -->
      <div class="tb-middle">
        <div class="tb-component-group">
          <a-tooltip title="视图/图表">
            <a-button type="text" class="tb-btn" @click="openChartSelector">
              <BarChartOutlined />
              <span class="tb-btn-label">图表</span>
            </a-button>
          </a-tooltip>
          <a-tooltip title="查询控件">
            <a-button type="text" class="tb-btn" @click="openFilterDialog">
              <FilterOutlined />
              <span class="tb-btn-label">过滤</span>
            </a-button>
          </a-tooltip>
          <a-tooltip title="富文本">
            <a-button type="text" class="tb-btn" @click="addTextComponent">
              <FontSizeOutlined />
              <span class="tb-btn-label">文本</span>
            </a-button>
          </a-tooltip>
          <a-tooltip title="媒体/网页">
            <a-button type="text" class="tb-btn" @click="openMediaDialog">
              <PictureOutlined />
              <span class="tb-btn-label">媒体</span>
            </a-button>
          </a-tooltip>
          <a-tooltip title="Tab/容器">
            <a-button type="text" class="tb-btn" @click="addContainer">
              <AppstoreOutlined />
              <span class="tb-btn-label">容器</span>
            </a-button>
          </a-tooltip>
          <a-tooltip title="组件复用">
            <a-button type="text" class="tb-btn" @click="openMultiplexing">
              <CopyFilled />
              <span class="tb-btn-label">复用</span>
            </a-button>
          </a-tooltip>
        </div>
      </div>

      <!-- Right Section -->
      <div class="tb-right">
        <a-tooltip title="仪表板配置">
          <a-button type="text" class="tb-btn" @click="openDashboardConfig">
            <SettingOutlined />
          </a-button>
        </a-tooltip>
        <a-tooltip title="隐藏组件">
          <a-button type="text" class="tb-btn" @click="openHiddenList">
            <EyeInvisibleOutlined />
          </a-button>
        </a-tooltip>
        <a-tooltip title="批量操作">
          <a-button type="text" class="tb-btn" :class="{ 'active-mode': batchMode }" @click="toggleBatchMode">
            <SelectOutlined />
          </a-button>
        </a-tooltip>
        <a-tooltip title="外部参数">
          <a-button type="text" class="tb-btn" @click="openExternalParams">
            <LinkOutlined />
          </a-button>
        </a-tooltip>
        <a-tooltip title="移动端配置">
          <a-button type="text" class="tb-btn" @click="openMobileConfig">
            <MobileOutlined />
          </a-button>
        </a-tooltip>
        <div class="tb-divider"></div>
        <a-dropdown>
          <a-button class="tb-btn">
            <EyeOutlined /> 预览
            <DownOutlined />
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="full" @click="previewFullscreen">全屏预览（当前页）</a-menu-item>
              <a-menu-item key="new" @click="previewNewPage">新页面预览</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-button class="tb-btn" @click="handleSave">
          <SaveOutlined /> 保存
        </a-button>
        <a-button type="primary" class="tb-btn" @click="handlePublish" v-if="store.dashboard?.status !== 'published'">
          <SendOutlined /> 发布
        </a-button>
        <a-dropdown v-else>
          <a-button type="primary" class="tb-btn">
            <CheckCircleOutlined /> 已发布
            <DownOutlined />
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="unpublish" @click="handleUnpublish">取消发布</a-menu-item>
              <a-menu-item key="restore" @click="handleRestorePublished">恢复到发布版</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>
    <!-- ========== Batch Toolbar ========== -->
    <Transition name="slide-down">
      <div class="batch-toolbar" v-if="batchMode">
        <span class="batch-info">已选择 {{ selectedBatchIds.length }} 个组件</span>
        <a-button size="small" @click="batchCopy">批量复制</a-button>
        <a-button size="small" danger @click="batchDelete">批量删除</a-button>
        <a-button size="small" type="link" @click="exitBatchMode">退出批量模式</a-button>
      </div>
    </Transition>

    <!-- ========== Editor Body ========== -->
    <div class="editor-body" v-if="!aiGenerating">
      <!-- Left Mini Dock (collapsed) -->
      <div class="left-mini-dock" :class="{ 'docked-expanded': leftDockExpanded }" @mouseenter="leftDockHovered = true" @mouseleave="leftDockHovered = false" v-if="leftSidebarCollapsed">
        <div class="mini-dock-icon" @click="toggleLeftSidebar" title="展开组件面板"><AppstoreOutlined /></div>
        <div class="mini-dock-divider"></div>
        <div class="mini-dock-icon" @click="handleDockSelectPanel" title="选择图表"><BorderOutlined /></div>
        <div class="mini-dock-icon" @click="openChartSelector" title="添加图表"><PlusOutlined /></div>
        <div class="mini-dock-divider"></div>
        <div class="mini-dock-bottom">
          <div class="mini-dock-icon" @click="showRightPanelViaDock" title="显示配置"><SettingOutlined /></div>
          <div class="mini-dock-icon expand-btn" @click="toggleLeftSidebar" title="展开面板"><RightOutlined /></div>
        </div>
      </div>

      <!-- Left Sidebar (full) -->
      <div class="left-sidebar-panel" :class="{ 'left-hidden': leftSidebarCollapsed }">
        <div class="left-sidebar-inner">
          <ComponentPalette
            :panels="store.panels"
            :selected-panel-id="store.selectedPanelId"
            @add-chart="handleAddChartFromPalette"
            @select-panel="handleLeftPanelSelect"
            @remove-panel="handleRemovePanel"
          />
        </div>
        <div class="sidebar-bottom-toggle">
          <div class="bottom-toggle-btn" @click="toggleLeftSidebar">
            <LeftOutlined v-if="!leftSidebarCollapsed" /><RightOutlined v-else />
          </div>
        </div>
      </div>

      <!-- Canvas -->
      <div class="editor-canvas-wrapper" @contextmenu="onCanvasContextMenu">
        <GlobalFilterBar :filters="store.filters" @filter-change="handleFilterChange" />

        <div ref="canvasElRef" class="editor-canvas" :style="canvasStyle" @drop.prevent.stop="onDrop" @dragover.prevent>
          <GridLayout
            v-if="store.dashboard"
            v-model:layout="layoutModel"
            :col-num="dashboardConfig.gridColumns"
            :row-height="dashboardConfig.gridRowHeight"
            :is-draggable="true"
            :is-resizable="true"
            :margin="[12, 12]"
            :vertical-compact="true"
            :use-css-transforms="true"
            @layout-updated="onLayoutUpdated"
          >
            <GridItem v-for="item in layoutModel" :key="item.i" :x="item.x" :y="item.y" :w="item.w" :h="item.h" :i="item.i">
              <PanelCard
                :panel="getPanel(item.i)"
                :selected="store.selectedPanelId === item.i || selectedBatchIds.includes(item.i)"
                :chart-data="getChartData(item.i)"
                :is-dark-mode="store.dashboard?.theme === 'dark'"
                @select="onCanvasPanelClick(item.i)"
                @edit="onEditPanel(item.i)"
                @copy="handleCopyPanel(item.i)"
                @hide="handleHidePanel(item.i)"
                @delete="handleRemovePanel(item.i)"
                @bringToFront="handleBringToFront(item.i)"
                @sendToBack="handleSendToBack(item.i)"
                @contextmenu="onPanelContextMenu"
              />
            </GridItem>
          </GridLayout>

          <a-empty v-if="store.panels.length === 0" description="拖动左侧图表组件到此处，或从图表列表添加" style="margin-top: 80px" />
        </div>
      </div>

      <!-- Right Config Panel -->
      <Transition name="slide-right-panel">
        <div class="right-float-panel" v-if="store.selectedPanel && rightPanelVisible">
          <div class="right-panel-header">
            <span class="right-panel-title">{{ store.selectedPanel.title || '图表配置' }}</span>
            <a-button type="text" size="small" @click="closeRightPanel"><CloseOutlined /></a-button>
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

    <!-- ========== AI Generating Overlay ========== -->
    <div class="ai-progress-overlay" v-else>
      <div class="ai-progress-card">
        <h3 class="ai-progress-title">AI 正在生成仪表板...</h3>
        <div class="ai-flow">
          <div v-for="(stage, idx) in aiStages" :key="stage.key" class="flow-stage" :class="stageClass(stage.key)">
            <div class="flow-stage-icon">
              <LoadingOutlined v-if="stageClass(stage.key) === 'stage-running'" />
              <CheckOutlined v-else-if="stageClass(stage.key) === 'stage-success'" />
              <CloseOutlined v-else-if="stageClass(stage.key) === 'stage-error'" />
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <span class="flow-stage-label">{{ stage.label }}</span>
          </div>
        </div>
        <a-progress :percent="aiProgress" :stroke-color="{ from: '#4F46E5', to: '#0891B2' }" :show-info="false" />
        <div class="ai-progress-status">{{ aiStatusText }}</div>
      </div>
    </div>

    <!-- ========== Modals & Dialogs ========== -->
    <DashboardConfigModal :open="dashboardConfigVisible" :dashboard="store.dashboard" @update:open="dashboardConfigVisible = $event" @apply="handleDashboardConfigApply" />
    <MultiplexingModal :open="multiplexingVisible" @update:open="multiplexingVisible = $event" @confirm="handleMultiplexingConfirm" />
    <HiddenListPanel :open="hiddenListVisible" :hidden-panels="hiddenPanels" @update:open="hiddenListVisible = $event" @restore="handleRestoreHidden" />

    <!-- Context Menu -->
    <ContextMenu :visible="contextMenuVisible" :x="contextMenuX" :y="contextMenuY" @update:visible="contextMenuVisible = $event" @action="handleContextAction" />
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowLeftOutlined, EditOutlined, UndoOutlined, RedoOutlined,
  BarChartOutlined, FilterOutlined, FontSizeOutlined, PictureOutlined,
  AppstoreOutlined, CopyFilled, SelectOutlined, SettingOutlined, EyeInvisibleOutlined,
  LinkOutlined, MobileOutlined, EyeOutlined, DownOutlined, SaveOutlined,
  SendOutlined, CheckCircleOutlined, CloseOutlined, PlusOutlined,
  LeftOutlined, RightOutlined, BorderOutlined, LoadingOutlined, CheckOutlined,
} from '@ant-design/icons-vue'
import { useVizStore } from '../../stores/viz_v2.js'
import { useSnapshot } from '../../composables/viz_v2/useSnapshot.js'
import ComponentPalette from '../../components/viz_v2/ComponentPalette.vue'
import PanelCard from '../../components/viz_v2/PanelCard.vue'
import PanelConfigPanel from '../../components/viz_v2/PanelConfigPanel.vue'
import GlobalFilterBar from '../../components/viz_v2/GlobalFilterBar.vue'
import DashboardConfigModal from '../../components/viz_v2/DashboardConfigModal.vue'
import MultiplexingModal from '../../components/viz_v2/MultiplexingModal.vue'
import HiddenListPanel from '../../components/viz_v2/HiddenListPanel.vue'
import ContextMenu from './components/ContextMenu.vue'
import { GridLayout, GridItem } from 'vue-grid-layout-v3'


const router = useRouter()
const route = useRoute()
const store = useVizStore()
const snapshot = useSnapshot()

// ─── State ────────────────────────────────────────
const editorName = ref('')
const isEditingName = ref(false)
const nameInputRef = ref(null)

const chartDataCache = ref({})
let isSyncingLayout = false

const canvasElRef = ref(null)

const layoutModel = computed({
  get: () => store.panels
    .filter(p => !p.hidden)
    .map(p => ({
      i: p.id,
      x: p.layout_x || 0,
      y: p.layout_y || 0,
      w: p.layout_w || 6,
      h: p.layout_h || 4,
    })),
  set: (newLayout) => {
    if (isSyncingLayout) return
    isSyncingLayout = true
    newLayout.forEach(item => {
      const panel = store.panels.find(p => p.id === item.i)
      if (panel) {
        panel.layout_x = item.x
        panel.layout_y = item.y
        panel.layout_w = item.w
        panel.layout_h = item.h
      }
    })
    nextTick(() => { isSyncingLayout = false })
  }
})

const leftSidebarCollapsed = ref(false)
const leftDockHovered = ref(false)
const leftDockExpanded = ref(false)
const rightPanelVisible = ref(false)
const rightSidebarCollapsed = ref(false)

const aiGenerating = ref(false)
const aiProgress = ref(0)
const aiStatusText = ref('')
const aiStages = ref([
  { key: 'analyze', label: '分析需求', status: 'pending' },
  { key: 'sql', label: '生成 SQL', status: 'pending' },
  { key: 'chart', label: '创建图表', status: 'pending' },
  { key: 'layout', label: '布局排版', status: 'pending' },
])

// Batch mode
const batchMode = ref(false)
const selectedBatchIds = ref([])

// Context menu
const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuPanelId = ref(null)

// Modals
const dashboardConfigVisible = ref(false)
const multiplexingVisible = ref(false)
const hiddenListVisible = ref(false)

// Dashboard config state
const dashboardConfig = reactive({
  canvasAdaption: 'width',
  canvasWidth: 1920,
  canvasHeight: 1080,
  backgroundColor: '#FFFFFF',
  backgroundOpacity: 1,
  backgroundImage: '',
  showGridLines: false,
  gridColumns: 12,
  gridRowHeight: 100,
})

// Hidden panels
const hiddenPanels = ref([])

// Computed
const canUndo = computed(() => snapshot.canUndo.value)
const canRedo = computed(() => snapshot.canRedo.value)

const canvasStyle = computed(() => ({
  backgroundColor: dashboardConfig.backgroundColor,
  opacity: dashboardConfig.backgroundOpacity,
  backgroundImage: dashboardConfig.backgroundImage ? url() : undefined,
  backgroundSize: dashboardConfig.backgroundImage ? 'cover' : undefined,
}))

// ─── Lifecycle ────────────────────────────────────
onMounted(async () => {
  const id = route.params.id || route.query.id
  if (id) {
    await store.loadDashboard(id)
    editorName.value = store.dashboard?.name || ''
    snapshot.initSnapshot(store.panels, store.filters)
    // Load dashboard config
    const d = store.dashboard
    if (d) {
      dashboardConfig.canvasAdaption = d.canvas_adaption || 'width'
      dashboardConfig.canvasWidth = d.canvas_width || 1920
      dashboardConfig.canvasHeight = d.canvas_height || 1080
      dashboardConfig.backgroundColor = d.background_color || '#FFFFFF'
      dashboardConfig.backgroundOpacity = d.background_opacity ?? 1
      dashboardConfig.backgroundImage = d.background_image || ''
      dashboardConfig.showGridLines = d.show_grid_lines ?? false
      dashboardConfig.gridColumns = d.grid_columns || 12
      dashboardConfig.gridRowHeight = d.grid_row_height || 100
    }
  }
})

// ─── Layout Helpers ───────────────────────────────
function getPanel(id) {
  return store.panels.find(p => p.id === id) || null
}

function getChartData(id) {
  if (chartDataCache.value[id]) return chartDataCache.value[id]
  const panel = store.panels.find(p => p.id === id)
  if (!panel) return null
  // Use panel's chart_type (set during add) even without chart_config_id
  return {
    chart_type: panel.chart_type || panel._chartType || 'bar',
    title: panel.title || '',
    sql_text: panel.sql_text || '',
    echarts_option: panel.echarts_option || {},
  }
}

// ─── Snapshot / Undo / Redo ──────────────────────────
function takeSnapshot() {
  snapshot.takeSnapshot(store.panels, store.filters)
}

async function handleUndo() {
  const changed = snapshot.undo(store.panels, store.filters)
  if (changed) {
    store.clearSelection()
  }
}

async function handleRedo() {
  const changed = snapshot.redo(store.panels, store.filters)
  if (changed) {
    store.clearSelection()
  }
}

// ─── Toolbar Actions ──────────────────────────────
function goBack() {
  if (store.dashboard) {
    router.push('/viz/dashboards')
  } else {
    router.push('/')
  }
}

function startEditName() {
  isEditingName.value = true
  nextTick(() => nameInputRef.value?.focus())
}
function finishEditName() { isEditingName.value = false }

async function openChartSelector() {
  if (!store.dashboard) return
  try {
    const panel = await store.addPanel(store.dashboard.id, null, '柱状图', { x: 0, y: 0, w: 6, h: 4 })
    if (panel) panel._chartType = 'bar'
    takeSnapshot()
  } catch (e) {
    store.panels.push({
      id: 'temp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title: '柱状图', _chartType: 'bar',
      layout_x: 0, layout_y: 0, layout_w: 6, layout_h: 4,
      hidden: false, chart_config_id: null,
    })
    takeSnapshot()
  }
}

function openFilterDialog() {
  console.log('打开过滤控件配置')
}

async function addTextComponent() {
  if (!store.dashboard) return
  try {
    const panel = await store.addPanel(store.dashboard.id, null, '文本', { x: 0, y: 0, w: 4, h: 2 })
    if (panel) panel._chartType = 'text'
    takeSnapshot()
  } catch (e) {
    store.panels.push({
      id: 'temp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title: '文本', _chartType: 'text',
      layout_x: 0, layout_y: 0, layout_w: 4, layout_h: 2,
      hidden: false, chart_config_id: null,
    })
    takeSnapshot()
  }
}

async function openMediaDialog() {
  if (!store.dashboard) return
  try {
    const panel = await store.addPanel(store.dashboard.id, null, '图片', { x: 0, y: 0, w: 6, h: 5 })
    if (panel) panel._chartType = 'image'
    takeSnapshot()
  } catch (e) {
    store.panels.push({
      id: 'temp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title: '图片', _chartType: 'image',
      layout_x: 0, layout_y: 0, layout_w: 6, layout_h: 5,
      hidden: false, chart_config_id: null,
    })
    takeSnapshot()
  }
}

async function addContainer() {
  if (!store.dashboard) return
  try {
    const panel = await store.addPanel(store.dashboard.id, null, '容器', { x: 0, y: 0, w: 12, h: 6 })
    if (panel) panel._chartType = 'container'
    takeSnapshot()
  } catch (e) {
    store.panels.push({
      id: 'temp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title: '容器', _chartType: 'container',
      layout_x: 0, layout_y: 0, layout_w: 12, layout_h: 6,
      hidden: false, chart_config_id: null,
    })
    takeSnapshot()
  }
}

function openMultiplexing() {
  multiplexingVisible.value = true
}

function openDashboardConfig() {
  dashboardConfigVisible.value = true
}

function openHiddenList() {
  hiddenListVisible.value = true
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedBatchIds.value = []
  }
}

function exitBatchMode() {
  batchMode.value = false
  selectedBatchIds.value = []
}

function openExternalParams() {
  console.log('打开外部参数配置')
}

function openMobileConfig() {
  console.log('打开移动端配置')
}

function previewFullscreen() {
  if (store.dashboard) {
    const url = router.resolve(`/viz/dashboards/${store.dashboard.id}/view`).href
    window.open(url, '_blank', 'fullscreen=yes')
  }
}

function previewNewPage() {
  if (store.dashboard) {
    router.push(`/viz/dashboards/${store.dashboard.id}/view`)
  }
}

async function handleSave() {
  try {
    if (editorName.value) {
      await store.saveDashboard({
        name: editorName.value,
        canvas_adaption: dashboardConfig.canvasAdaption,
        canvas_width: dashboardConfig.canvasWidth,
        canvas_height: dashboardConfig.canvasHeight,
        background_color: dashboardConfig.backgroundColor,
        background_opacity: dashboardConfig.backgroundOpacity,
        background_image: dashboardConfig.backgroundImage,
        show_grid_lines: dashboardConfig.showGridLines,
        grid_columns: dashboardConfig.gridColumns,
        grid_row_height: dashboardConfig.gridRowHeight,
      })
    }
    await store.updateLayout(layoutModel.value)
    takeSnapshot()
  } catch (e) { console.error('保存失败', e) }
}

async function handlePublish() {
  try {
    await store.saveDashboard({ status: 'published' })
  } catch (e) { console.error('发布失败', e) }
}

async function handleUnpublish() {
  try {
    await store.saveDashboard({ status: 'draft' })
  } catch (e) { console.error('取消发布失败', e) }
}

async function handleRestorePublished() {
  try {
    await store.loadDashboard(store.dashboard.id)
    takeSnapshot()
  } catch (e) { console.error('恢复失败', e) }
}

// ─── Sidebar ──────────────────────────────────────
function toggleLeftSidebar() {
  leftSidebarCollapsed.value = !leftSidebarCollapsed.value
}

function showRightPanel() {
  rightPanelVisible.value = true
}

function closeRightPanel() {
  rightPanelVisible.value = false
  store.clearSelection()
}

function handleLeftPanelSelect(panelId) {
  store.selectPanel(panelId)
  showRightPanel()
  nextTick(() => {
    if (!rightPanelVisible.value && store.selectedPanel) {
      rightPanelVisible.value = true
    }
  })
}

function handleDockSelectPanel() {
  const first = store.panels.find(p => !p.hidden)
  if (first) { store.selectPanel(first.id); showRightPanel() }
}

function showRightPanelViaDock() {
  if (store.selectedPanel) { showRightPanel() } else { handleDockSelectPanel() }
}

// ─── Canvas Panel Actions ─────────────────────────
function onCanvasPanelClick(panelId) {
  if (batchMode.value) {
    const idx = selectedBatchIds.value.indexOf(panelId)
    if (idx >= 0) { selectedBatchIds.value.splice(idx, 1) }
    else { selectedBatchIds.value.push(panelId) }
    return
  }
  store.selectPanel(panelId)
  showRightPanel()
}

function onEditPanel(panelId) {
  store.selectPanel(panelId)
  showRightPanel()
}

async function handleAddChartFromPalette(chartType) {
  if (!store.dashboard) return
  
  const chartTypeNames = {
    bar: '柱状图', line: '折线图', pie: '饼图', doughnut: '环形图',
    scatter: '散点图', radar: '雷达图', funnel: '漏斗图', gauge: '仪表盘',
    number_card: '数字卡片', table: '数据表格', heatmap: '热力图',
    text: '文本', image: '图片', video: '视频', iframe: '网页', container: '容器'
  }
  const title = chartTypeNames[chartType] || chartType || '图表'
  
  try {
    const panel = await store.addPanel(store.dashboard.id, null, title, { x: 0, y: 0, w: 6, h: 4 })
    if (panel) panel._chartType = chartType
    takeSnapshot()
  } catch (e) {
    console.error('添加面板失败', e)
    const tempId = 'temp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8)
    store.panels.push({
      id: tempId,
      title,
      _chartType: chartType,
      layout_x: 0, layout_y: 0, layout_w: 6, layout_h: 4,
      hidden: false,
      chart_config_id: null,
    })
    takeSnapshot()
  }
}

async function handleRemovePanel(panelId) {
  if (!store.dashboard) return
  try {
    await store.removePanel(store.dashboard.id, panelId)
    delete chartDataCache.value[panelId]
    selectedBatchIds.value = selectedBatchIds.value.filter(id => id !== panelId)
    takeSnapshot()
  } catch (e) {
    console.error('删除面板失败', e)
  }
}

async function handleCopyPanel(panelId) {
  const panel = store.panels.find(p => p.id === panelId)
  if (!panel || !store.dashboard) return
  try {
    const copied = await store.addPanel(store.dashboard.id, panel.chart_config_id, (panel.title || '图表') + ' (副本)', {
      x: (panel.layout_x || 0) + 1,
      y: (panel.layout_y || 0) + 1,
      w: panel.layout_w || 6,
      h: panel.layout_h || 4,
    })
    if (copied) copied._chartType = panel._chartType || panel.chart_type
    takeSnapshot()
  } catch (e) { console.error('复制面板失败', e) }
}

function handleBringToFront(panelId) {
  const idx = store.panels.findIndex(p => p.id === panelId)
  if (idx > 0) {
    const [item] = store.panels.splice(idx, 1)
    store.panels.unshift(item)
    takeSnapshot()
  }
}

function handleSendToBack(panelId) {
  const idx = store.panels.findIndex(p => p.id === panelId)
  if (idx >= 0 && idx < store.panels.length - 1) {
    const [item] = store.panels.splice(idx, 1)
    store.panels.push(item)
    takeSnapshot()
  }
}

// ─── Layout Events ────────────────────────────────
function onLayoutUpdated(newLayout) {
  store.updateLayout(newLayout).catch(() => {})
}

function calcDropGridXY(clientX, clientY) {
  if (!canvasElRef.value) return { x: 0, y: 0 }
  const rect = canvasElRef.value.getBoundingClientRect()
  const cols = dashboardConfig.gridColumns
  const rowH = dashboardConfig.gridRowHeight
  const marginX = 12
  const marginY = 12
  const pad = 16

  const relX = clientX - rect.left - pad
  const relY = clientY - rect.top - pad

  const totalColWidth = rect.width - pad * 2
  const colUnit = (totalColWidth - marginX * (cols - 1)) / cols

  const col = Math.max(0, Math.min(cols - 1, Math.round(relX / (colUnit + marginX))))
  const row = Math.max(0, Math.round(relY / (rowH + marginY)))

  return { x: col, y: row }
}

async function onDrop(event) {
  const chartType = event.dataTransfer.getData('chartType')
  if (!chartType || !store.dashboard) return

  const { x, y } = calcDropGridXY(event.clientX, event.clientY)

  const chartTypeNames = {
    bar: '柱状图', line: '折线图', pie: '饼图', doughnut: '环形图',
    scatter: '散点图', radar: '雷达图', funnel: '漏斗图', gauge: '仪表盘',
    number_card: '数字卡片', table: '数据表格', heatmap: '热力图',
    text: '文本', image: '图片', video: '视频', iframe: '网页', container: '容器'
  }
  const title = chartTypeNames[chartType] || chartType || '图表'
  
  try {
    const panel = await store.addPanel(store.dashboard.id, null, title, { x, y, w: 6, h: 4 })
    if (panel) panel._chartType = chartType
    takeSnapshot()
  } catch (e) {
    console.error('添加面板失败', e)
    const tempId = 'temp_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8)
    store.panels.push({
      id: tempId,
      title,
      _chartType: chartType,
      layout_x: x, layout_y: y, layout_w: 6, layout_h: 4,
      hidden: false,
      chart_config_id: null,
    })
    takeSnapshot()
  }
}

// ─── Batch Operations ─────────────────────────────
async function batchCopy() {
  for (const pid of selectedBatchIds.value) {
    await handleCopyPanel(pid)
  }
  selectedBatchIds.value = []
}

async function batchDelete() {
  for (const pid of [...selectedBatchIds.value]) {
    await handleRemovePanel(pid)
  }
  selectedBatchIds.value = []
  exitBatchMode()
}

// ─── Context Menu ─────────────────────────────────
function onCanvasContextMenu(e) {
  // Only show context menu if clicking on empty canvas area
  if (e.target.closest('.panel-card')) return
  contextMenuX.value = e.clientX
  contextMenuY.value = e.clientY
  contextMenuVisible.value = true
}

function onPanelContextMenu({ x, y, panelId }) {
  contextMenuX.value = x
  contextMenuY.value = y
  contextMenuPanelId.value = panelId
  contextMenuVisible.value = true
}

function handleContextAction(action) {
  const pid = contextMenuPanelId.value || store.selectedPanelId
  if (!pid) return
  switch (action) {
    case 'copy': handleCopyPanel(pid); break
    case 'delete': handleRemovePanel(pid); break
    case 'bringToFront': handleBringToFront(pid); break
    case 'sendToBack': handleSendToBack(pid); break
  }
  contextMenuVisible.value = false
}

async function handleHidePanel(panelId) {
  const panel = store.panels.find(p => p.id === panelId)
  if (!panel) return
  panel.hidden = true
  hiddenPanels.value.push(panel)
  await store.updatePanelConfig(panelId, { hidden: true })
}

function handleRestoreHidden(panelId) {
  const panel = hiddenPanels.value.find(p => p.id === panelId)
  if (panel) {
    panel.hidden = false
    hiddenPanels.value = hiddenPanels.value.filter(p => p.id !== panelId)
  }
}

// ─── Config Panel ─────────────────────────────────
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
    takeSnapshot()
  } catch (e) { console.error('应用配置失败', e) }
}

function handleExecuteSql() {
  console.log('执行SQL')
}

// ─── Filter ───────────────────────────────────────
function handleFilterChange(filterEvent) {
  console.log('筛选器变化', filterEvent)
}

// ─── Dashboard Config ─────────────────────────────
function handleDashboardConfigApply(config) {
  Object.assign(dashboardConfig, config)
}

// ─── Multiplexing (Component Reuse) ───────────────
async function handleMultiplexingConfirm({ dashboardId, panelId }) {
  if (!store.dashboard) return
  try {
    const res = await fetch(`/api/viz/dashboards/${dashboardId}`)
    if (!res.ok) throw new Error('加载源仪表板失败')
    const data = await res.json()
    const sourcePanel = (data.panels || []).find(p => p.id === panelId)
    if (sourcePanel) {
      await store.addPanel(store.dashboard.id, sourcePanel.chart_config_id,
        (sourcePanel.title || '图表') + ' (复用)', {
        x: 0, y: 0, w: sourcePanel.layout_w || 6, h: sourcePanel.layout_h || 4,
      })
      takeSnapshot()
    }
  } catch (e) { console.error('复用组件失败', e) }
}

// ─── AI Generation Stages ─────────────────────────
function stageClass(stageKey) {
  const found = aiStages.value.find(s => s.key === stageKey)
  if (!found) return ''
  const status = found.status
  if (status === 'running') return 'stage-running'
  if (status === 'success') return 'stage-success'
  if (status === 'error') return 'stage-error'
  return ''
}

// ─── Watch for Hidden Panel Changes ──────────────
watch(() => store.panels.filter(p => p.hidden).length, () => {
  // Layout model auto-updates via computed
})
</script>
<style scoped>

/* === Vue Grid Layout Required Styles (导入必要样式) === */
:deep(.vue-grid-layout) {
  position: relative;
  transition: height 200ms ease;
}
:deep(.vue-grid-item) {
  transition: all 200ms ease;
  transition-property: left, top, width, height;
}
:deep(.vue-grid-item.no-touch) {
  touch-action: none;
}
:deep(.vue-grid-item.cssTransforms) {
  transition-property: transform;
  left: 0;
  right: auto;
}
:deep(.vue-grid-item.resizing) {
  opacity: 0.6;
  z-index: 3;
}
:deep(.vue-grid-item.vue-draggable-dragging) {
  transition: none;
  z-index: 3;
}
:deep(.vue-grid-item > .vue-resizable-handle) {
  position: absolute;
  width: 20px;
  height: 20px;
  bottom: 0;
  right: 0;
  background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMSAxMGw5LTlNMCA5bDEwLTEwTTAgNWwxMC0xMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjOTk5IiBzdHJva2Utd2lkdGg9IjIiLz48L3N2Zz4=') no-repeat bottom right;
  padding: 0 3px 3px 0;
  background-origin: content-box;
  box-sizing: border-box;
  cursor: se-resize;
}
:deep(.vue-grid-item > .vue-resizable-handle.vue-resizable-handle-sw) {
  bottom: 0;
  left: 0;
  cursor: sw-resize;
  transform: rotate(90deg);
}
:deep(.vue-grid-item > .vue-resizable-handle.vue-resizable-handle-nw) {
  top: 0;
  left: 0;
  cursor: nw-resize;
  transform: rotate(180deg);
}
:deep(.vue-grid-item > .vue-resizable-handle.vue-resizable-handle-ne) {
  top: 0;
  right: 0;
  cursor: ne-resize;
  transform: rotate(270deg);
}
:deep(.vue-grid-placeholder) {
  background: var(--color-primary);
  opacity: 0.15;
  transition-duration: 100ms;
  z-index: 2;
  border-radius: 4px;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  -o-user-select: none;
  user-select: none;
}


/* ─── Root Layout ───────────────────────────────── */
.dashboard-editor {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  display: flex; flex-direction: column;
  background: var(--color-bg-page);
  font-family: var(--font-sans);
}
.dashboard-editor.dark-theme { background: var(--color-sidebar-bg); color: var(--color-text-inverse); }

/* ─── Toolbar ──────────────────────────────────── */
.editor-toolbar {
  display: flex; align-items: center;
  padding: 0 12px; height: 44px;
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0; z-index: 100;
  box-shadow: var(--shadow-sm);
  gap: 4px;
  user-select: none;
}
.dark-theme .editor-toolbar { background: var(--color-sidebar-hover); border-color: rgba(255,255,255,0.06); }
.dark-theme .editor-toolbar .tb-btn { color: rgba(255,255,255,0.65); }
.dark-theme .editor-toolbar .tb-btn:hover { color: rgba(255,255,255,0.9); background: rgba(255,255,255,0.08); }

.tb-left, .tb-right { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.tb-middle { flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.tb-component-group { display: flex; align-items: center; gap: 2px; }

.tb-btn {
  display: inline-flex; align-items: center; gap: 4px;
  height: 32px; padding: 4px 10px;
  border: none; border-radius: var(--radius-sm);
  font-size: 13px; cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary); background: transparent;
}
.tb-btn:hover { background: rgba(0,0,0,0.04); color: var(--color-text-primary); }
.tb-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.tb-btn.active-mode { color: var(--color-primary); background: var(--color-primary-light); }
.tb-btn-label { font-size: 12px; }

.tb-divider { width: 1px; height: 20px; background: var(--color-border); margin: 0 6px; }

.dark-theme .tb-divider { background: rgba(255,255,255,0.1); }

/* Name editing */
.name-display {
  display: flex; align-items: center; gap: 6px;
  cursor: pointer; padding: 2px 8px; border-radius: var(--radius-sm);
  transition: background var(--transition-fast); font-size: 14px; font-weight: 600;
}
.name-display:hover { background: rgba(0,0,0,0.04); }
.dark-theme .name-display:hover { background: rgba(255,255,255,0.06); }
.name-edit-icon { font-size: 13px; color: var(--color-text-tertiary); }
.name-input { width: 200px; font-size: 14px; font-weight: 600; }
.dark-theme .name-input { background: transparent; color: var(--color-text-inverse); }

/* ─── Batch Toolbar ──────────────────────────────── */
.batch-toolbar {
  display: flex; align-items: center; gap: 12px;
  padding: 6px 16px; height: 40px;
  background: var(--color-primary-light);
  border-bottom: 1px solid var(--color-primary);
  flex-shrink: 0;
}
.dark-theme .batch-toolbar { background: rgba(79,70,229,0.15); border-color: rgba(79,70,229,0.3); }
.batch-info { font-size: 13px; font-weight: 500; color: var(--color-primary); margin-right: auto; }

/* ─── Editor Body ────────────────────────────────── */
.editor-body {
  flex: 1; display: flex; overflow: hidden; position: relative;
}

/* ─── Left Mini Dock ─────────────────────────────── */
.left-mini-dock {
  width: 40px; display: flex; flex-direction: column; align-items: center;
  padding: 8px 0; background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border-light);
  flex-shrink: 0; z-index: 50;
  transition: width 0.2s;
}
.dark-theme .left-mini-dock { background: var(--color-sidebar-hover); border-color: rgba(255,255,255,0.06); }
.mini-dock-icon {
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-sm); cursor: pointer; font-size: 16px;
  color: var(--color-text-tertiary); transition: all var(--transition-fast);
}
.mini-dock-icon:hover { background: rgba(0,0,0,0.05); color: var(--color-text-primary); }
.dark-theme .mini-dock-icon:hover { background: rgba(255,255,255,0.08); color: var(--color-text-inverse); }
.mini-dock-divider { width: 20px; height: 1px; background: var(--color-border); margin: 6px 0; }
.dark-theme .mini-dock-divider { background: rgba(255,255,255,0.08); }
.mini-dock-bottom { margin-top: auto; display: flex; flex-direction: column; align-items: center; gap: 4px; }

/* ─── Left Sidebar ───────────────────────────────── */
.left-sidebar-panel {
  width: 240px; display: flex; flex-direction: column;
  border-right: 1px solid var(--color-border-light);
  background: var(--color-bg-surface); flex-shrink: 0;
  transition: width 0.25s ease, opacity 0.2s; overflow: hidden;
}
.dark-theme .left-sidebar-panel { background: var(--color-sidebar-hover); border-color: rgba(255,255,255,0.06); }
.left-sidebar-panel.left-hidden { width: 0; opacity: 0; padding: 0; border: none; }
.left-sidebar-inner { flex: 1; overflow-y: auto; }
.sidebar-bottom-toggle { display: flex; justify-content: flex-end; padding: 4px; border-top: 1px solid var(--color-border-light); }
.dark-theme .sidebar-bottom-toggle { border-color: rgba(255,255,255,0.06); }
.bottom-toggle-btn {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; border-radius: var(--radius-sm); color: var(--color-text-tertiary); font-size: 12px;
  transition: all var(--transition-fast);
}
.bottom-toggle-btn:hover { background: rgba(0,0,0,0.05); }
.dark-theme .bottom-toggle-btn:hover { background: rgba(255,255,255,0.08); }

/* ─── Canvas ─────────────────────────────────────── */
.editor-canvas-wrapper {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
  background: var(--color-bg-page);
}
.dark-theme .editor-canvas-wrapper { background: var(--color-sidebar-bg); }
.editor-canvas {
  flex: 1; overflow: auto; padding: 16px;
  background-repeat: no-repeat; background-position: center;
  min-height: 400px;
}


/* ─── Right Config Panel ─────────────────────────── */
.right-float-panel {
  width: 320px; display: flex; flex-direction: column;
  border-left: 1px solid var(--color-border-light);
  background: var(--color-bg-surface); flex-shrink: 0;
  z-index: 30; overflow: hidden;
}
.dark-theme .right-float-panel { background: var(--color-sidebar-hover); border-color: rgba(255,255,255,0.06); }
.right-panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-bottom: 1px solid var(--color-border-light); flex-shrink: 0;
}
.dark-theme .right-panel-header { border-color: rgba(255,255,255,0.06); }
.right-panel-title { font-size: 14px; font-weight: 600; }
.right-panel-body { flex: 1; overflow-y: auto; }

/* ─── Transitions ────────────────────────────────── */
.slide-right-enter-active, .slide-right-leave-active { transition: width 0.25s ease, opacity 0.2s; }
.slide-right-enter-from, .slide-right-leave-to { width: 0 !important; opacity: 0; overflow: hidden; }
.slide-down-enter-active, .slide-down-leave-active { transition: height 0.2s ease, opacity 0.15s; overflow: hidden; }
.slide-down-enter-from, .slide-down-leave-to { height: 0 !important; opacity: 0; padding: 0; }

/* ─── AI Progress Overlay ────────────────────────── */
.ai-progress-overlay {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background: var(--color-bg-page);
}
.dark-theme .ai-progress-overlay { background: var(--color-sidebar-bg); }
.ai-progress-card {
  background: var(--color-bg-surface); border-radius: 12px; padding: 32px 40px;
  min-width: 560px; max-width: 700px; box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}
.dark-theme .ai-progress-card { background: var(--color-sidebar-hover); box-shadow: 0 4px 24px rgba(0,0,0,0.3); }
.ai-progress-title { margin: 0 0 24px; font-size: 18px; font-weight: 600; color: var(--color-text-primary); text-align: center; }
.dark-theme .ai-progress-title { color: rgba(255,255,255,0.9); }
.ai-flow { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 20px; flex-wrap: wrap; }
.flow-stage { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 10px 14px; border-radius: 8px; min-width: 70px; border: 2px solid transparent; background: rgba(0,0,0,0.02); transition: all 0.25s ease; }
.dark-theme .flow-stage { background: rgba(255,255,255,0.03); }
.flow-stage-icon { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600; background: rgba(0,0,0,0.06); color: var(--color-text-tertiary); transition: all 0.25s ease; }
.dark-theme .flow-stage-icon { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.35); }
.stage-running { background: rgba(79,70,229,0.08); border-color: var(--color-primary); box-shadow: 0 0 12px rgba(79,70,229,0.2); }
.dark-theme .stage-running { background: rgba(129,140,248,0.12); border-color: #818cf8; box-shadow: 0 0 16px rgba(129,140,248,0.25); }
.stage-running .flow-stage-icon { background: var(--color-primary); color: #fff; }
.stage-success { background: rgba(82,196,26,0.04); border-color: rgba(82,196,26,0.2); }
.stage-success .flow-stage-icon { background: #52c41a; color: #fff; }
.stage-error { background: rgba(255,77,79,0.06); border-color: rgba(255,77,79,0.3); }
.stage-error .flow-stage-icon { background: #ff4d4f; color: #fff; }
.flow-stage-label { font-size: 13px; font-weight: 500; color: var(--color-text-secondary); white-space: nowrap; }
.stage-running .flow-stage-label { color: var(--color-primary); font-weight: 600; }
.stage-success .flow-stage-label { color: #52c41a; }
.flow-arrow { display: flex; align-items: center; padding: 0 4px; font-size: 16px; color: var(--color-text-tertiary); margin-top: 8px; }
.dark-theme .flow-arrow { color: rgba(255,255,255,0.25); }
.ai-progress-status { text-align: center; margin-top: 12px; font-size: 13px; color: var(--color-text-secondary); }

/* ─── Dark Theme Overrides ───────────────────────── */
.dark-theme .name-display { color: var(--color-text-inverse); }
.dark-theme .name-edit-icon { color: rgba(255,255,255,0.4); }
.dark-theme .editor-canvas-wrapper :deep(.panel-card) { background: var(--color-sidebar-hover); }
.dark-theme .editor-canvas-wrapper :deep(.chart-title) { color: rgba(255,255,255,0.85); }
.dark-theme .editor-canvas-wrapper :deep(.chart-type-tag) { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.5); }
</style>
