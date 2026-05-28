<template>
  <div class="screen-editor-layout" @keydown="handleKeyDown" tabindex="0">
    <!-- 顶部工具栏 -->
    <div class="editor-header">
      <div class="header-left">
        <a-button type="text" @click="router.back()">
          <LeftOutlined /> 返回
        </a-button>
        <span class="screen-title">数据大屏编辑器</span>
      </div>
      <div class="header-center">
        <a-space>
          <a-tooltip title="缩小">
            <a-button @click="scale -= 0.1"><MinusOutlined /></a-button>
          </a-tooltip>
          <span class="scale-text">{{ Math.round(scale * 100) }}%</span>
          <a-tooltip title="放大">
            <a-button @click="scale += 0.1"><PlusOutlined /></a-button>
          </a-tooltip>
          <a-tooltip title="适应屏幕">
            <a-button @click="fitScale"><ExpandOutlined /></a-button>
          </a-tooltip>
        </a-space>
      </div>
      <div class="header-right">
        <a-space>
          <a-button>预览</a-button>
          <a-button type="primary" @click="saveScreen">保存</a-button>
        </a-space>
      </div>
    </div>

    <div class="editor-main">
      <!-- 左侧区域：组件库与图层 -->
      <div class="editor-sidebar left-sidebar">
        <a-tabs v-model:activeKey="leftTab">
          <a-tab-pane key="components" tab="组件库">
            <div class="component-list">
              <div
                class="component-item"
                draggable="true"
                @dragstart="handleDragStart($event, 'bar-chart')"
              >
                <BarChartOutlined /> 柱状图
              </div>
              <div
                class="component-item"
                draggable="true"
                @dragstart="handleDragStart($event, 'line-chart')"
              >
                <LineChartOutlined /> 折线图
              </div>
              <div
                class="component-item"
                draggable="true"
                @dragstart="handleDragStart($event, 'number-card')"
              >
                <NumberOutlined /> 数字卡片
              </div>
              <div
                class="component-item"
                draggable="true"
                @dragstart="handleDragStart($event, 'text')"
              >
                <FontSizeOutlined /> 文本块
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane key="layers" tab="图层">
            <div class="layer-list">
              <div
                v-for="(comp, index) in components.slice().reverse()"
                :key="comp.id"
                class="layer-item"
                :class="{ active: activeComponent?.id === comp.id }"
                @click="activeComponent = comp"
              >
                {{ comp.name || comp.type }} - 层级 {{ comp.component_data.z }}
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>

      <!-- 中心画布区域 -->
      <div 
        class="editor-canvas-container" 
        ref="canvasContainer" 
        @mousedown="clearSelection"
        @contextmenu.prevent="showCanvasMenu"
        @dragover.prevent="handleDragOver"
        @drop="handleDrop"
      >
        <div
          class="canvas-board"
          :style="canvasStyle"
        >
          <Shape
            v-for="comp in components"
            :key="comp.id"
            :active="activeComponent?.id === comp.id"
            :defaultStyle="comp.component_data"
            :scale="scale"
            @update:style="updateComponentStyle(comp.id, $event)"
            @mousedown.stop="selectComponent(comp)"
            @contextmenu.stop.prevent="showComponentMenu($event, comp)"
          >
            <ComponentWrapper :config="comp" />
          </Shape>
        </div>
      </div>

      <!-- 右侧区域：属性面板 -->
      <div class="editor-sidebar right-sidebar">
        <a-tabs v-if="activeComponent" v-model:activeKey="rightTab">
          <a-tab-pane key="style" tab="样式">
            <a-form layout="vertical" size="small" class="prop-form">
              <div class="prop-group">
                <div class="group-title">基础属性</div>
                <a-form-item label="组件名称">
                  <a-input v-model:value="activeComponent.name" />
                </a-form-item>
                <a-row :gutter="8">
                  <a-col :span="12">
                    <a-form-item label="X 坐标">
                      <a-input-number v-model:value="activeComponent.component_data.x" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="Y 坐标">
                      <a-input-number v-model:value="activeComponent.component_data.y" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="宽度">
                      <a-input-number v-model:value="activeComponent.component_data.w" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="高度">
                      <a-input-number v-model:value="activeComponent.component_data.h" />
                    </a-form-item>
                  </a-col>
                </a-row>
              </div>

              <div class="prop-group" v-if="activeComponent.type === 'text'">
                <div class="group-title">内容设置</div>
                <a-form-item label="文本内容">
                  <a-textarea v-model:value="activeComponent.propValue" :rows="3" />
                </a-form-item>
              </div>
            </a-form>
          </a-tab-pane>
          <a-tab-pane key="data" tab="数据">
            <div style="padding: 16px; color: #888">
              数据绑定功能开发中...
            </div>
          </a-tab-pane>
        </a-tabs>

        <a-tabs v-else v-model:activeKey="canvasTab">
          <a-tab-pane key="canvas" tab="画板">
            <a-form layout="vertical" size="small" class="prop-form">
              <div class="prop-group">
                <div class="group-title">数据大屏基础设置</div>
                <a-row :gutter="8">
                  <a-col :span="12">
                    <a-form-item label="宽度">
                      <a-input-number v-model:value="canvasConfig.width" @change="fitScale" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="高度">
                      <a-input-number v-model:value="canvasConfig.height" @change="fitScale" />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-form-item label="背景颜色">
                  <input type="color" v-model="canvasConfig.backgroundColor" style="width: 100%" />
                </a-form-item>
              </div>
            </a-form>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 右键菜单 -->
    <ContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @update:visible="contextMenu.visible = $event"
      @action="handleContextAction"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { LeftOutlined, ExpandOutlined, PlusOutlined, MinusOutlined, BarChartOutlined, LineChartOutlined, FontSizeOutlined, NumberOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import Shape from './components/Shape.vue'
import ComponentWrapper from './components/ComponentWrapper.vue'
import ContextMenu from './components/ContextMenu.vue'

const router = useRouter()
const leftTab = ref('components')
const rightTab = ref('style')
const canvasTab = ref('canvas')

// 画布配置
const canvasConfig = ref({
  width: 1920,
  height: 1080,
  backgroundColor: '#0f172a'
})

// 缩放
const canvasContainer = ref(null)
const scale = ref(1)

const canvasStyle = computed(() => ({
  width: `${canvasConfig.value.width}px`,
  height: `${canvasConfig.value.height}px`,
  backgroundColor: canvasConfig.value.backgroundColor,
  transform: `scale(${scale.value})`,
  transformOrigin: '0 0'
}))

const fitScale = () => {
  if (!canvasContainer.value) return
  const { clientWidth, clientHeight } = canvasContainer.value
  const padding = 100
  const scaleX = (clientWidth - padding) / canvasConfig.value.width
  const scaleY = (clientHeight - padding) / canvasConfig.value.height
  scale.value = Math.min(scaleX, scaleY, 1)
}

onMounted(() => {
  window.addEventListener('resize', fitScale)
  setTimeout(fitScale, 100)
})
onUnmounted(() => window.removeEventListener('resize', fitScale))

// 组件数据
const components = ref([])
const activeComponent = ref(null)


// Drag over handler to allow dropping with visual feedback
const handleDragOver = (e) => {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'copy'
}

const createComponent = (type, x = 100, y = 100) => {
  const typeNameMap = {
    'text': { name: '文 本', w: 300, h: 150 },
    'bar-chart': { name: '柱 状 图', w: 400, h: 300 },
    'line-chart': { name: '折 线 图', w: 400, h: 300 },
    'number-card': { name: '数 字 卡 片', w: 200, h: 120 }
  }
  const defaults = typeNameMap[type] || { name: type, w: 400, h: 300 }
  const z = components.value.length + 1
  return {
    id: `comp_${Date.now()}`,
    type,
    name: defaults.name,
    propValue: type === 'text' ? '双 击 编 辑 文 本' : (type === 'number-card' ? 0 : ''),
    component_data: { x, y, z, w: defaults.w, h: defaults.h }
  }
}

const selectComponent = (comp) => {
  activeComponent.value = comp
}

const clearSelection = () => {
  activeComponent.value = null
}

const updateComponentStyle = (id, style) => {
  const comp = components.value.find(c => c.id === id)
  if (comp) {
    comp.component_data = style
  }
}

// 拖拽加入
const handleDragStart = (e, type) => {
  e.dataTransfer.setData('componentType', type)
}

const handleDrop = (e) => {
  const type = e.dataTransfer.getData('componentType') || e.dataTransfer.getData('text/plain')
  if (!type) return
  
  // 计算基于画布的坐标
  const rect = document.querySelector('.canvas-board').getBoundingClientRect()
  const x = (e.clientX - rect.left) / scale.value
  const y = (e.clientY - rect.top) / scale.value
  
  const newComp = createComponent(type, Math.round(x), Math.round(y))
  components.value.push(newComp)
  activeComponent.value = newComp
}

// 剪贴板
const clipboard = ref(null)

// 快捷键
const handleKeyDown = (e) => {
  if (e.target.nodeName === 'INPUT' || e.target.nodeName === 'TEXTAREA') return

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (activeComponent.value) {
      components.value = components.value.filter(c => c.id !== activeComponent.value.id)
      activeComponent.value = null
    }
  } else if (e.ctrlKey && e.key === 'c') {
    if (activeComponent.value) {
      clipboard.value = JSON.parse(JSON.stringify(activeComponent.value))
      message.success('已复制')
    }
  } else if (e.ctrlKey && e.key === 'v') {
    if (clipboard.value) {
      const newComp = JSON.parse(JSON.stringify(clipboard.value))
      newComp.id = `comp_${Date.now()}`
      newComp.component_data.x += 20
      newComp.component_data.y += 20
      newComp.component_data.z = components.value.length + 1
      components.value.push(newComp)
      activeComponent.value = newComp
    }
  }
}

// 右键菜单
const contextMenu = ref({ visible: false, x: 0, y: 0, target: null })

const showCanvasMenu = (e) => {
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    target: 'canvas'
  }
}

const showComponentMenu = (e, comp) => {
  selectComponent(comp)
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    target: 'component'
  }
}

const handleContextAction = (action) => {
  if (!activeComponent.value && contextMenu.value.target !== 'canvas') return

  if (action === 'copy') {
    clipboard.value = JSON.parse(JSON.stringify(activeComponent.value))
    message.success('已复制')
  } else if (action === 'paste') {
    if (clipboard.value) {
      const newComp = JSON.parse(JSON.stringify(clipboard.value))
      newComp.id = `comp_${Date.now()}`
      
      if (contextMenu.value.target === 'canvas') {
        const rect = document.querySelector('.canvas-board').getBoundingClientRect()
        newComp.component_data.x = Math.round((contextMenu.value.x - rect.left) / scale.value)
        newComp.component_data.y = Math.round((contextMenu.value.y - rect.top) / scale.value)
      } else {
        newComp.component_data.x += 20
        newComp.component_data.y += 20
      }
      newComp.component_data.z = components.value.length + 1
      components.value.push(newComp)
      activeComponent.value = newComp
    }
  } else if (action === 'delete') {
    components.value = components.value.filter(c => c.id !== activeComponent.value.id)
    activeComponent.value = null
  } else if (['top', 'bottom', 'up', 'down'].includes(action)) {
    adjustZIndex(action)
  }
}

const adjustZIndex = (type) => {
  const comp = activeComponent.value
  const maxZ = components.value.length
  
  if (type === 'top') {
    comp.component_data.z = maxZ + 1
  } else if (type === 'bottom') {
    comp.component_data.z = 0
  } else if (type === 'up') {
    comp.component_data.z += 1
  } else if (type === 'down') {
    comp.component_data.z = Math.max(0, comp.component_data.z - 1)
  }
  
  // 重新排列Z Index使其连续
  components.value.sort((a, b) => a.component_data.z - b.component_data.z)
  components.value.forEach((c, index) => {
    c.component_data.z = index + 1
  })
}

const saveScreen = () => {
  message.success('数据大屏已保存')
}
</script>

<style scoped>
.screen-editor-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
  outline: none; /* for keydown */
}
.editor-header {
  height: 56px;
  background: #252526;
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}
.header-left, .header-right { width: 250px; }
.header-center { flex: 1; text-align: center; }
.screen-title { margin-left: 12px; font-weight: 600; color: #fff; }
.scale-text { color: #ccc; font-size: 13px; min-width: 40px; display: inline-block; }

.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.editor-sidebar {
  width: 280px;
  background: #252526;
  display: flex;
  flex-direction: column;
}
.left-sidebar { border-right: 1px solid #333; }
.right-sidebar { border-left: 1px solid #333; }

/* 画布容器 */
.editor-canvas-container {
  flex: 1 1 auto;
  background: #1e1e1e;
  position: relative;
  overflow: auto;
  display: block;
  white-space: nowrap;
  text-align: center;
}
.canvas-board {
  display: inline-block;
  vertical-align: middle;
  white-space: normal;
  position: relative;
  background: #0f172a;
  box-shadow: 0 0 20px rgba(0,0,0,0.8);
  margin: auto;
}

/* 组件库 */
.component-list { padding: 16px; display: grid; gap: 12px; grid-template-columns: 1fr 1fr; }
.component-item {
  background: #333; padding: 12px 8px; text-align: center; border-radius: 4px; cursor: grab;
  border: 1px solid transparent;
}
.component-item:hover { background: #444; border-color: #1890ff; color: #1890ff; }

/* 图层列表 */
.layer-list { padding: 8px; overflow-y: auto; }
.layer-item {
  padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #333; font-size: 13px;
}
.layer-item:hover { background: #2a2d33; }
.layer-item.active { background: #17385b; color: #1890ff; border-left: 3px solid #1890ff; }

/* 属性面板 */
.prop-form { padding: 16px; }
.prop-group { margin-bottom: 24px; }
.group-title { font-weight: 600; color: #fff; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #444; }

:deep(.ant-tabs-nav) { margin-bottom: 0 !important; }
:deep(.ant-tabs-tab) { color: #d4d4d4 !important; }
:deep(.ant-tabs-tab-active) { color: #1890ff !important; }
:deep(.ant-form-item-label > label) { color: #ccc !important; }
:deep(.ant-input), :deep(.ant-input-number) { background: #333; color: #fff; border-color: #444; }
:deep(.ant-input:focus), :deep(.ant-input-number:focus) { border-color: #1890ff; }
</style>
