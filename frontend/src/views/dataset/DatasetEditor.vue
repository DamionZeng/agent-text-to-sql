<template>
  <div class="dataset-editor">
    <!-- Header -->
    <div class="editor-header">
      <div class="header-left">
        <a-button type="text" @click="router.back()">
          <LeftOutlined /> 返回
        </a-button>
        <span class="divider">|</span>
        <a-input 
          v-model:value="formData.name" 
          placeholder="请输入数据集名称" 
          class="dataset-name-input"
          :bordered="false"
        />
      </div>
      <div class="header-right">
        <a-space>
          <a-button @click="router.back()">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">保存</a-button>
        </a-space>
      </div>
    </div>

    <div class="editor-main">
      <!-- Left Sidebar -->
      <div class="datasource-sidebar">
        <div class="sidebar-section">
          <div class="section-title">选择数据源</div>
          <a-select 
            v-model:value="formData.datasource_id" 
            @change="onDatasourceChange" 
            placeholder="选择数据源"
            style="width: 100%"
            class="ds-select"
          >
            <a-select-option v-for="ds in datasources" :key="ds.id" :value="ds.id">
              {{ ds.name }}
            </a-select-option>
          </a-select>
        </div>

        <div class="sidebar-section table-section">
          <div class="section-header">
            <span class="section-title">数据表</span>
            <span class="table-count" v-if="schemaTables.length">{{ schemaTables.length }}</span>
          </div>
          
          <div 
            class="table-item custom-sql-item" 
            :class="{ active: formData.type === 'custom_sql' }"
            @click="selectCustomSql"
          >
            <CodeOutlined class="table-icon" />
            <span class="table-name">自定义 SQL</span>
          </div>

          <div class="search-box">
            <a-input v-model:value="tableSearch" placeholder="搜索物理表" size="small">
              <template #prefix><SearchOutlined style="color: #bfbfbf" /></template>
            </a-input>
          </div>
          
          <div class="table-list">
            <div 
              v-for="table in filteredTables" 
              :key="table.name" 
              class="table-item"
              :class="{ active: formData.type === 'db_table' && currentSelectedTableName === table.name }"
              draggable="true"
              @dragstart="handleDragStart($event, table)"
              @click="onTableSelect(table.name)"
            >
              <TableOutlined class="table-icon" />
              <span class="table-name" :title="table.name">{{ table.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div class="content-area">
        <!-- Modeling Canvas / SQL Editor -->
        <div class="modeling-area">
          <div v-if="formData.type === 'custom_sql'" class="sql-editor-container">
            <div class="sql-toolbar">
              <span class="toolbar-title">SQL 编辑器</span>
              <a-button type="primary" size="small" @click="runSql" :loading="runningSql">
                <CaretRightOutlined /> 执行查询
              </a-button>
            </div>
            <div class="sql-editor-wrapper">
              <a-textarea 
                v-model:value="formData.info.sql" 
                placeholder="在此输入 SQL 查询..." 
                class="sql-textarea"
              />
            </div>
          </div>
          
          <div 
            v-else 
            class="join-canvas" 
            ref="canvasRef"
            @dragover.prevent="handleDragOver"
            @drop="handleDrop"
            @mousedown="onCanvasMouseDown"
          >
            <!-- SVG Layer for Links -->
            <svg class="canvas-svg">
              <path 
                v-for="(link, idx) in tableLinks" 
                :key="'link_'+idx"
                :d="getLinkPath(link)"
                class="join-curve"
              />
            </svg>

            <div v-if="canvasTables.length === 0" class="canvas-placeholder">
              <div class="placeholder-content">
                <CloudUploadOutlined class="placeholder-icon" />
                <p>将左侧表拖拽至此进行关联建模</p>
              </div>
            </div>

            <!-- Nodes -->
            <div 
              v-for="(table, index) in canvasTables" 
              :key="table.id"
              class="canvas-table-node"
              :class="{ 
                active: currentSelectedTableName === table.name,
                highlighted: highlightedNodeId === table.id
              }"
              :style="{ left: table.x + 'px', top: table.y + 'px' }"
              @mousedown.stop="onNodeMouseDown($event, table)"
              @click.stop="onTableSelect(table.name)"
            >
              <div class="node-header">
                <TableOutlined />
                <span class="node-name">{{ table.name }}</span>
                <CloseOutlined class="node-close" @click.stop="removeTable(index)" />
              </div>
            </div>
          </div>
        </div>

        <!-- Metadata & Preview & Join Config Area -->
        <div class="bottom-area">
          <div class="bottom-main">
            <div class="bottom-header">
              <a-tabs v-model:activeKey="activeBottomTab" class="bottom-tabs">
                <a-tab-pane key="metadata" tab="元数据" />
                <a-tab-pane key="preview" tab="数据预览" />
              </a-tabs>
            </div>

            <div class="bottom-body">
              <!-- Metadata Module -->
              <div v-if="activeBottomTab === 'metadata'" class="metadata-container">
                <div v-if="!currentMetadata.table" class="empty-state">
                  <a-empty description="选择表以查看元数据" />
                </div>
                <div v-else class="metadata-content">
                  <div class="meta-table-info">
                    <h3>{{ currentMetadata.table.name }} <span class="meta-alias" v-if="currentMetadata.table.alias">({{ currentMetadata.table.alias }})</span></h3>
                    <p class="meta-desc">{{ currentMetadata.table.description || '无表描述' }}</p>
                  </div>
                  <a-table 
                    :columns="metaColumns" 
                    :data-source="currentMetadata.columns" 
                    size="small" 
                    :pagination="false"
                    class="meta-table"
                    :scroll="{ y: 'calc(100vh - 550px)' }"
                  />
                </div>
              </div>

              <!-- Preview Module -->
              <div v-if="activeBottomTab === 'preview'" class="preview-container">
                <div v-if="!previewData.length" class="empty-state">
                  <a-empty description="模型尚未配置或无数据预览" />
                </div>
                <a-table
                  v-else
                  :columns="previewColumns"
                  :data-source="previewData"
                  :pagination="false"
                  size="small"
                  bordered
                  :scroll="{ x: 'max-content', y: 'calc(100vh - 480px)' }"
                  :loading="runningSql"
                />
              </div>
            </div>
          </div>

          <!-- Join Configuration Module (Right Side) -->
          <div v-if="tableLinks.length > 0" class="join-config-panel">
            <div class="panel-header">关联配置</div>
            <div class="panel-body">
              <div v-for="(link, idx) in tableLinks" :key="'link_cfg_'+idx" class="join-config-item">
                <div class="join-title">
                  <span class="t-name">{{ getTableNameById(link.from) }}</span>
                  <SwapOutlined />
                  <span class="t-name">{{ getTableNameById(link.to) }}</span>
                </div>
                <a-form layout="vertical" size="small">
                  <a-form-item label="关联类型">
                    <a-select v-model:value="link.type">
                      <a-select-option value="inner">Inner Join</a-select-option>
                      <a-select-option value="left">Left Join</a-select-option>
                      <a-select-option value="right">Right Join</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="左表字段">
                    <a-select v-model:value="link.leftField" placeholder="选择字段">
                      <a-select-option v-for="c in getColumnsById(link.from)" :key="c.name" :value="c.name">{{ c.name }}</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="右表字段">
                    <a-select v-model:value="link.rightField" placeholder="选择字段">
                      <a-select-option v-for="c in getColumnsById(link.to)" :key="c.name" :value="c.name">{{ c.name }}</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-form>
                <a-divider v-if="idx < tableLinks.length - 1" style="margin: 12px 0" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  LeftOutlined, SearchOutlined, TableOutlined, CodeOutlined, CaretRightOutlined,
  CloudUploadOutlined, CloseOutlined, CaretDownOutlined, SwapOutlined
} from '@ant-design/icons-vue'
import { useDataset } from '../../composables/dataset/useDataset'

const router = useRouter()
const route = useRoute()
const { fetchDatasources, fetchDatasourceSchema, executeSql, fetchTableMetadata, createDataset } = useDataset()

const canvasRef = ref(null)
const saving = ref(false)
const runningSql = ref(false)
const datasources = ref([])
const schemaTables = ref([])
const tableSearch = ref('')
const activeBottomTab = ref('metadata')
const canvasTables = ref([])
const tableLinks = ref([])
const previewData = ref([])
const currentMetadata = ref({ table: null, columns: [] })
const currentSelectedTableName = ref(null)
const highlightedNodeId = ref(null)

const formData = reactive({
  name: '',
  description: '',
  datasource_id: undefined,
  type: 'db_table',
  info: { table_name: undefined, sql: '' },
  fields: []
})

const filteredTables = computed(() => {
  if (!tableSearch.value) return schemaTables.value
  return schemaTables.value.filter(t => t.name.toLowerCase().includes(tableSearch.value.toLowerCase()))
})

const previewColumns = computed(() => {
  return formData.fields.map(f => ({
    title: f.name,
    dataIndex: f.origin_name,
    key: f.origin_name,
    width: 150
  }))
})

const metaColumns = [
  { title: '字段名', dataIndex: 'name', key: 'name' },
  { title: '别名', dataIndex: 'alias', key: 'alias' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '角色', dataIndex: 'role', key: 'role' }
]

onMounted(async () => {
  try {
    datasources.value = await fetchDatasources()
  } catch (err) {
    message.error('初始化失败')
  }
})

const onDatasourceChange = async (dsId) => {
  formData.info.table_name = undefined
  formData.fields = []
  canvasTables.value = []
  tableLinks.value = []
  previewData.value = []
  currentMetadata.value = { table: null, columns: [] }
  currentSelectedTableName.value = null
  try {
    const schema = await fetchDatasourceSchema(dsId)
    schemaTables.value = schema.tables || []
  } catch (err) {
    message.error('加载结构失败')
    schemaTables.value = []
  }
}

const selectCustomSql = () => {
  formData.type = 'custom_sql'
  formData.info.table_name = undefined
  activeBottomTab.value = 'preview'
  currentSelectedTableName.value = null
}

const onTableSelect = async (tableName) => {
  formData.type = 'db_table'
  currentSelectedTableName.value = tableName
  formData.info.table_name = tableName
  const table = schemaTables.value.find(t => t.name === tableName)
  if (table) {
    updateFieldsFromSchema(table.columns)
    fetchRealPreview(`SELECT * FROM ${tableName} LIMIT 50`)
    loadMetadata(tableName)
  }
}

const loadMetadata = async (tableName) => {
  if (!formData.datasource_id) return
  try {
    const meta = await fetchTableMetadata(formData.datasource_id, tableName)
    currentMetadata.value = meta
  } catch (err) {
    console.error('Meta load failed', err)
  }
}

const updateFieldsFromSchema = (columns) => {
  formData.fields = columns.map(col => ({
    origin_name: col.name,
    name: col.name,
    data_type: col.type,
    checked: true
  }))
}

// Node Interaction
const handleDragStart = (e, table) => {
  e.dataTransfer.setData('table', JSON.stringify(table))
}

const handleDragOver = (e) => {
  const rect = canvasRef.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  // Find proximity for highlighting
  const nearest = findNearestNode(mouseX, mouseY)
  highlightedNodeId.value = nearest ? nearest.id : null
}

const handleDrop = (e) => {
  const tableData = e.dataTransfer.getData('table')
  if (!tableData) return
  const table = JSON.parse(tableData)
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left - 75
  const y = e.clientY - rect.top - 20
  
  formData.type = 'db_table'
  
  const newNode = {
    ...table,
    id: 'node_' + Date.now() + Math.floor(Math.random()*100),
    x,
    y
  }
  
  // Proximity join logic
  const targetNode = findNearestNode(x + 75, y + 20)
  
  canvasTables.value.push(newNode)
  
  if (targetNode) {
    tableLinks.value.push({
      from: targetNode.id,
      to: newNode.id,
      type: 'inner',
      leftField: null,
      rightField: null
    })
    message.success(`已与 ${targetNode.name} 建立连接`)
  }

  if (canvasTables.value.length === 1) {
    onTableSelect(table.name)
  }
  highlightedNodeId.value = null
}

const findNearestNode = (x, y) => {
  let nearest = null
  let minDistance = 150 // Proximity threshold
  
  canvasTables.value.forEach(node => {
    const dx = node.x + 75 - x
    const dy = node.y + 20 - y
    const dist = Math.sqrt(dx*dx + dy*dy)
    if (dist < minDistance) {
      minDistance = dist
      nearest = node
    }
  })
  return nearest
}

const removeTable = (index) => {
  const tableId = canvasTables.value[index].id
  canvasTables.value.splice(index, 1)
  // Remove associated links
  tableLinks.value = tableLinks.value.filter(l => l.from !== tableId && l.to !== tableId)
  
  if (canvasTables.value.length === 0) {
    formData.info.table_name = undefined
    formData.fields = []
    previewData.value = []
    currentMetadata.value = { table: null, columns: [] }
    currentSelectedTableName.value = null
  } else {
    onTableSelect(canvasTables.value[0].name)
  }
}

// Move Node
let activeNode = null
let dragStartPos = { x: 0, y: 0 }

const onNodeMouseDown = (e, table) => {
  activeNode = table
  dragStartPos = { x: e.clientX - table.x, y: e.clientY - table.y }
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const onMouseMove = (e) => {
  if (activeNode) {
    activeNode.x = e.clientX - dragStartPos.x
    activeNode.y = e.clientY - dragStartPos.y
  }
}

const onMouseUp = () => {
  activeNode = null
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
}

const onCanvasMouseDown = (e) => {
  currentSelectedTableName.value = null
}

// Link Path Rendering
const getLinkPath = (link) => {
  const from = canvasTables.value.find(t => t.id === link.from)
  const to = canvasTables.value.find(t => t.id === link.to)
  if (!from || !to) return ''
  
  const startX = from.x + 150
  const startY = from.y + 20
  const endX = to.x
  const endY = to.y + 20
  
  const cp1x = startX + (endX - startX) / 2
  const cp2x = startX + (endX - startX) / 2
  
  return `M ${startX} ${startY} C ${cp1x} ${startY}, ${cp2x} ${endY}, ${endX} ${endY}`
}

const getTableNameById = (id) => canvasTables.value.find(t => t.id === id)?.name || ''
const getColumnsById = (id) => canvasTables.value.find(t => t.id === id)?.columns || []

// SQL Actions
const runSql = async () => {
  if (!formData.info.sql || !formData.datasource_id) return
  runningSql.value = true
  try {
    const results = await executeSql(formData.datasource_id, formData.info.sql)
    previewData.value = results
    if (results.length > 0) {
      const keys = Object.keys(results[0])
      formData.fields = keys.map(k => ({
        origin_name: k,
        name: k,
        checked: true
      }))
    }
  } catch (err) {
    message.error(err.message)
  } finally {
    runningSql.value = false
  }
}

const fetchRealPreview = async (sql) => {
  if (!formData.datasource_id) return
  runningSql.value = true
  try {
    const results = await executeSql(formData.datasource_id, sql)
    previewData.value = results
  } catch (err) {
    console.error('Preview failed', err)
  } finally {
    runningSql.value = false
  }
}

const handleSave = async () => {
  if (!formData.name || !formData.datasource_id || (!formData.info.table_name && !formData.info.sql)) {
    return message.warning('请填写完整的必要信息')
  }
  saving.value = true
  try {
    await createDataset(formData)
    message.success('数据集创建成功')
    router.push('/dataset/list')
  } catch (err) {
    message.error(err.message || '创建失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.dataset-editor {
  height: 100vh; display: flex; flex-direction: column; background: #f0f2f5; color: #262626;
}

.editor-header {
  height: 48px; background: #fff; border-bottom: 1px solid #d9d9d9;
  display: flex; align-items: center; justify-content: space-between; padding: 0 16px; flex-shrink: 0;
}
.header-left { display: flex; align-items: center; flex: 1; }
.divider { margin: 0 12px; color: #d9d9d9; }
.dataset-name-input { font-size: 16px; font-weight: 500; width: 300px; }

.editor-main { flex: 1; display: flex; overflow: hidden; }

.datasource-sidebar {
  width: 240px; background: #fff; border-right: 1px solid #d9d9d9; display: flex; flex-direction: column;
}
.sidebar-section { padding: 16px; border-bottom: 1px solid #f0f0f0; }
.section-title { font-size: 12px; font-weight: 500; color: #8c8c8c; margin-bottom: 8px; display: block; }
.section-header {
  display: flex; align-items: center; justify-content: space-between;

}
.table-count { font-size: 11px; color: #8c8c8c; background: #f5f5f5; padding: 0 6px; border-radius: 10px; }
.search-box { margin: 8px 0 12px; }

.custom-sql-item { margin-bottom: 8px !important; border: 1px dashed #d9d9d9; justify-content: center; color: #1890ff; }
.custom-sql-item.active { border-style: solid; background: #e6f7ff; }

.table-list { flex: 1; overflow-y: auto; padding: 0 8px 16px; }
.table-item {
  padding: 8px 12px; display: flex; align-items: center; cursor: pointer; border-radius: 4px;
  transition: all 0.2s; margin: 2px 0; font-size: 13px;
}
.table-item:hover { background: #f5f5f5; }
.table-item.active { background: #e6f7ff; color: #1890ff; }
.table-icon { margin-right: 8px; }

.content-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.modeling-area { height: 350px; background: #fff; border-bottom: 1px solid #d9d9d9; flex-shrink: 0; position: relative; }

.join-canvas {
  height: 100%; width: 100%; background: #fafafa; 
  background-image: radial-gradient(#d9d9d9 1px, transparent 1px);
  background-size: 20px 20px; position: relative;
}
.canvas-svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
.join-curve { fill: none; stroke: #1890ff; stroke-width: 2; stroke-dasharray: 4; }

.canvas-placeholder { position: absolute; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #bfbfbf; }
.placeholder-icon { font-size: 48px; margin-bottom: 12px; }

.canvas-table-node {
  position: absolute; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; width: 150px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); cursor: move; transition: border-color 0.2s, box-shadow 0.2s;
  z-index: 10;
}
.canvas-table-node:hover { border-color: #1890ff; }
.canvas-table-node.active { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }
.canvas-table-node.highlighted { border-color: #52c41a; box-shadow: 0 0 8px rgba(82,196,26,0.5); }

.node-header {
  padding: 8px 12px; background: #f5f5f5; border-bottom: 1px solid #f0f0f0;
  display: flex; align-items: center; gap: 8px; font-size: 12px;
}
.node-name { flex: 1; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-close { font-size: 10px; cursor: pointer; color: #8c8c8c; }
.node-close:hover { color: #ff4d4f; }

.sql-editor-container { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.sql-toolbar {
  height: 40px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #f0f0f0; flex-shrink: 0;
}
.sql-editor-wrapper { flex: 1; min-height: 0; }
.sql-textarea {
  height: 100%; width: 100%; border: none; resize: none; font-family: monospace;
  font-size: 14px; padding: 12px; background: #282c34; color: #abb2bf;
  outline: none;
}

.bottom-area { flex: 1; display: flex; overflow: hidden; background: #fff; }
.bottom-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.bottom-header { height: 40px; border-bottom: 1px solid #f0f0f0; padding: 0 16px; }
.bottom-tabs :deep(.ant-tabs-nav) { margin-bottom: 0; }
.bottom-body { flex: 1; overflow: hidden; display: flex; }

.metadata-container { flex: 1; display: flex; flex-direction: column; padding: 16px; overflow-y: auto; }
.meta-table-info h3 { margin-bottom: 4px; }
.meta-alias { color: #8c8c8c; font-size: 14px; }
.meta-desc { color: #595959; margin-bottom: 16px; }

.preview-container { flex: 1; overflow: hidden; padding: 16px; }
.empty-state { height: 100%; display: flex; align-items: center; justify-content: center; }

.join-config-panel {
  width: 280px; border-left: 1px solid #d9d9d9; background: #fafafa; display: flex; flex-direction: column;
}
.panel-header { padding: 12px 16px; font-weight: 600; border-bottom: 1px solid #f0f0f0; background: #fff; }
.panel-body { flex: 1; overflow-y: auto; padding: 16px; }
.join-title { 
  display: flex; align-items: center; gap: 8px; margin-bottom: 16px; font-size: 12px; 
  color: #1890ff; font-weight: 500; justify-content: center;
}
.t-name { max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;


}
:deep(.ant-table-thead > tr > th) { background: #fafafa; }

</style>
