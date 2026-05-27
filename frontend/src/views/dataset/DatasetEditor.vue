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
        <a-tag v-if="currentGroupName" color="blue" class="group-tag">
          <FolderOutlined /> {{ currentGroupName }}
        </a-tag>
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
                <a-tab-pane key="joins" tab="关联配置" v-if="tableLinks.length > 0" />
              </a-tabs>
              <div class="header-actions">
                <a-button size="small" type="primary" ghost @click="refreshData" :loading="runningSql">
                  <ReloadOutlined /> 刷新数据
                </a-button>
              </div>
            </div>

            <div class="bottom-body">
              <!-- Metadata Module -->
              <div v-if="activeBottomTab === 'metadata'" class="metadata-container">
                <div v-if="!currentMetadata.table" class="empty-state">
                  <a-empty description="选择左侧或画布中的表以管理字段" />
                </div>
                <div v-else class="metadata-content">
                  <div class="meta-table-info">
                    <div class="meta-title-row">
                      <h3>{{ currentMetadata.table.name }} <span class="meta-alias" v-if="currentMetadata.table.alias">({{ currentMetadata.table.alias }})</span></h3>
                      <a-checkbox 
                        :checked="isTableAllSelected(currentMetadata.table.name)"
                        :indeterminate="isTableIndeterminate(currentMetadata.table.name)"
                        @change="toggleTableFields(currentMetadata.table.name)"
                      >
                        全选/反选
                      </a-checkbox>
                    </div>
                    <p class="meta-desc">{{ currentMetadata.table.description || '无表描述' }}</p>
                  </div>
                  <a-table 
                    :columns="metaColumns" 
                    :data-source="getTableFields(currentMetadata.table.name)" 
                    size="small" 
                    :pagination="false"
                    class="meta-table"
                    row-key="origin_name"
                    :scroll="{ y: 'calc(100vh - 550px)' }"
                  >
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.key === 'checked'">
                        <a-checkbox v-model:checked="record.checked" @change="onFieldCheckChange" />
                      </template>
                    </template>
                  </a-table>
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

              <!-- Join Configuration Module -->
              <div v-if="activeBottomTab === 'joins'" class="join-config-container">
                <div class="join-cards-grid">
                  <div v-for="(link, idx) in tableLinks" :key="'link_cfg_'+idx" class="join-card">
                    <div class="join-card-header">
                      <div class="table-tag-node left">{{ getTableNameById(link.from) }}</div>
                      <div class="join-connector">
                        <span class="join-type-label">{{ link.type.toUpperCase() }}</span>
                        <div class="connector-line"></div>
                      </div>
                      <div class="table-tag-node right">{{ getTableNameById(link.to) }}</div>
                    </div>
                    <div class="join-card-content">
                      <a-row :gutter="32">
                        <a-col :span="8">
                          <div class="input-label">关联类型</div>
                          <a-select v-model:value="link.type" style="width: 100%" @change="onJoinConfigChange">
                            <a-select-option value="inner">Inner Join</a-select-option>
                            <a-select-option value="left">Left Join</a-select-option>
                            <a-select-option value="right">Right Join</a-select-option>
                          </a-select>
                        </a-col>
                        <a-col :span="8">
                          <div class="input-label">左表字段 ({{ getTableNameById(link.from) }})</div>
                          <a-select v-model:value="link.leftField" placeholder="选择字段" style="width: 100%" @change="onJoinConfigChange">
                            <a-select-option v-for="c in getTableFieldsById(link.from)" :key="c.origin_name" :value="c.origin_name">{{ c.origin_name }}</a-select-option>
                          </a-select>
                        </a-col>
                        <a-col :span="8">
                          <div class="input-label">右表字段 ({{ getTableNameById(link.to) }})</div>
                          <a-select v-model:value="link.rightField" placeholder="选择字段" style="width: 100%" @change="onJoinConfigChange">
                            <a-select-option v-for="c in getTableFieldsById(link.to)" :key="c.origin_name" :value="c.origin_name">{{ c.origin_name }}</a-select-option>
                          </a-select>
                        </a-col>
                      </a-row>
                    </div>
                  </div>
                </div>
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
  CloudUploadOutlined, CloseOutlined, CaretDownOutlined, SwapOutlined, ReloadOutlined,
  FolderOutlined
} from '@ant-design/icons-vue'
import { useDataset } from '../../composables/dataset/useDataset'

const router = useRouter()
const route = useRoute()
const { fetchDatasources, fetchDatasourceSchema, executeSql, fetchTableMetadata, createDataset, updateDataset, fetchDataset, fetchGroups } = useDataset()

const canvasRef = ref(null)
const saving = ref(false)
const runningSql = ref(false)
const datasources = ref([])
const groups = ref([])
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
  group_id: route.query.group_id || undefined,
  type: 'db_table',
  info: { table_name: undefined, sql: '', canvasTables: [], tableLinks: [] },
  fields: [],
  status: 'active'
})

const currentGroupName = computed(() => {
  if (!formData.group_id) return null
  const group = groups.value.find(g => g.id === formData.group_id)
  return group ? group.name : null
})

const filteredTables = computed(() => {
  if (!tableSearch.value) return schemaTables.value
  return schemaTables.value.filter(t => t.name.toLowerCase().includes(tableSearch.value.toLowerCase()))
})

const previewColumns = computed(() => {
  if (previewData.value.length === 0) return []
  const firstRow = previewData.value[0]
  return Object.keys(firstRow).map(key => ({
    title: key,
    dataIndex: key,
    key: key,
    width: 150
  }))
})

const metaColumns = [
  { title: '启用', dataIndex: 'checked', key: 'checked', width: 60, align: 'center' },
  { title: '字段名', dataIndex: 'origin_name', key: 'origin_name' },
  { title: '显示名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'data_type', key: 'type' },
  { title: '描述', dataIndex: 'description', key: 'description' }
]

onMounted(async () => {
  try {
    const [dsData, groupData] = await Promise.all([
      fetchDatasources(),
      fetchGroups()
    ])
    datasources.value = dsData
    groups.value = groupData

    if (route.params.id) {
      const data = await fetchDataset(route.params.id)
      formData.name = data.name
      formData.datasource_id = data.datasource_id
      formData.group_id = data.group_id
      formData.type = data.type
      formData.description = data.description
      formData.fields = data.fields || []
      formData.info = data.info || { sql: '', canvasTables: [], tableLinks: [] }
      
      if (formData.datasource_id) {
        await onDatasourceChange(formData.datasource_id)
        if (formData.info.canvasTables) {
          canvasTables.value = formData.info.canvasTables
        }
        if (formData.info.tableLinks) {
          tableLinks.value = formData.info.tableLinks
        }
        if (formData.type === 'db_table' && formData.info.table_name) {
          await onTableSelect(formData.info.table_name)
        } else if (formData.type === 'custom_sql' && formData.info.sql) {
          await runSql()
        }
      }
    }
  } catch (err) {
    message.error('初始化失败: ' + err.message)
  }
})

const onDatasourceChange = async (dsId) => {
  if (!route.params.id || canvasTables.value.length === 0) {
    formData.info.table_name = undefined
    formData.fields = []
    canvasTables.value = []
    tableLinks.value = []
    previewData.value = []
    currentMetadata.value = { table: null, columns: [] }
    currentSelectedTableName.value = null
  }
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
  
  // Auto-add to canvas if empty
  if (table && canvasTables.value.length === 0) {
    const newNode = {
      ...table,
      id: 'node_' + Date.now(),
      x: 100,
      y: 100
    }
    canvasTables.value.push(newNode)
  }

  if (table) {
    // Only add if not already in fields
    if (!formData.fields.some(f => f.tableName === tableName)) {
      const newFields = table.columns.map(col => ({
        tableName: tableName,
        origin_name: col.name,
        name: col.name,
        data_type: col.type,
        checked: true
      }))
      formData.fields.push(...newFields)
    }
    loadMetadata(tableName)
    // Fetch preview if it's the only table
    if (canvasTables.value.length <= 1) {
      fetchRealPreview(`SELECT * FROM ${tableName} LIMIT 50`)
    }
  }
}

const loadMetadata = async (tableName) => {
  if (!formData.datasource_id) return
  try {
    const meta = await fetchTableMetadata(formData.datasource_id, tableName)
    currentMetadata.value = meta
    // Update descriptions in formData.fields if available
    if (meta.columns) {
      meta.columns.forEach(mc => {
        const field = formData.fields.find(f => f.tableName === tableName && f.origin_name === mc.name)
        if (field) {
          field.description = mc.description
          field.name = mc.alias || field.name
          field.role = mc.role
        }
      })
    }
  } catch (err) {
    console.error('Meta load failed', err)
  }
}

// Field Management Helpers
const getTableFields = (tableName) => {
  return formData.fields.filter(f => f.tableName === tableName)
}

const isTableAllSelected = (tableName) => {
  const fields = getTableFields(tableName)
  return fields.length > 0 && fields.every(f => f.checked)
}

const isTableIndeterminate = (tableName) => {
  const fields = getTableFields(tableName)
  const checkedCount = fields.filter(f => f.checked).length
  return checkedCount > 0 && checkedCount < fields.length
}

const toggleTableFields = (tableName) => {
  const allSelected = isTableAllSelected(tableName)
  formData.fields.forEach(f => {
    if (f.tableName === tableName) f.checked = !allSelected
  })
  onFieldCheckChange()
}

const onFieldCheckChange = () => {
  if (formData.type === 'db_table') {
    formData.info.sql = generateJoinSql()
  }
}

const onJoinConfigChange = () => {
  if (formData.type === 'db_table') {
    formData.info.sql = generateJoinSql()
  }
}

// SQL Generation Logic
const generateJoinSql = () => {
  if (canvasTables.value.length === 0) return ''
  
  const selectedFields = formData.fields.filter(f => f.checked)
  const selectClause = selectedFields.length > 0 
    ? selectedFields.map(f => `${f.tableName}.${f.origin_name} AS "${f.tableName}.${f.origin_name}"`).join(', ')
    : '*'

  if (canvasTables.value.length === 1) {
    return `SELECT ${selectClause} FROM ${canvasTables.value[0].name}`
  }
  
  let sql = `SELECT ${selectClause} FROM ${canvasTables.value[0].name}`
  
  tableLinks.value.forEach(link => {
    const fromTable = canvasTables.value.find(t => t.id === link.from)
    const toTable = canvasTables.value.find(t => t.id === link.to)
    if (fromTable && toTable) {
      const joinType = link.type === 'inner' ? 'INNER JOIN' : (link.type === 'left' ? 'LEFT JOIN' : 'RIGHT JOIN')
      const condition = (link.leftField && link.rightField) 
        ? `ON ${fromTable.name}.${link.leftField} = ${toTable.name}.${link.rightField}` 
        : 'ON 1=1'
      sql += `\n${joinType} ${toTable.name} ${condition}`
    }
  })
  return sql
}

const refreshData = async () => {
  if (formData.type === 'custom_sql') {
    await runSql()
  } else {
    const generatedSql = generateJoinSql()
    if (generatedSql) {
      formData.info.sql = generatedSql
      await fetchRealPreview(generatedSql)
      activeBottomTab.value = 'preview'
      message.success('数据已刷新')
    }
  }
}

// Node Interaction
const handleDragStart = (e, table) => {
  e.dataTransfer.setData('table', JSON.stringify(table))
}

const handleDragOver = (e) => {
  const rect = canvasRef.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
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
  
  const targetNode = findNearestNode(x + 75, y + 20)
  canvasTables.value.push(newNode)
  
  // Also ensure fields are loaded when dropped
  onTableSelect(table.name)

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

  highlightedNodeId.value = null
}

const findNearestNode = (x, y) => {
  let nearest = null
  let minDistance = 150
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
  const tableName = canvasTables.value[index].name
  canvasTables.value.splice(index, 1)
  tableLinks.value = tableLinks.value.filter(l => l.from !== tableId && l.to !== tableId)
  
  // Remove fields of this table if it's the only instance
  if (!canvasTables.value.some(t => t.name === tableName)) {
    formData.fields = formData.fields.filter(f => f.tableName !== tableName)
  }
  
  if (canvasTables.value.length === 0) {
    formData.info.table_name = undefined
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

const onCanvasMouseDown = () => {
  currentSelectedTableName.value = null
}

const getLinkPath = (link) => {
  const from = canvasTables.value.find(t => t.id === link.from)
  const to = canvasTables.value.find(t => t.id === link.to)
  if (!from || !to) return ''
  const startX = from.x + 160
  const startY = from.y + 20
  const endX = to.x
  const endY = to.y + 20
  const cp1x = startX + (endX - startX) / 2
  const cp2x = startX + (endX - startX) / 2
  return `M ${startX} ${startY} C ${cp1x} ${startY}, ${cp2x} ${endY}, ${endX} ${endY}`
}

const getTableNameById = (id) => canvasTables.value.find(t => t.id === id)?.name || ''
const getTableFieldsById = (id) => {
  const name = getTableNameById(id)
  return getTableFields(name)
}

const runSql = async () => {
  if (!formData.info.sql || !formData.datasource_id) return
  runningSql.value = true
  try {
    const results = await executeSql(formData.datasource_id, formData.info.sql)
    previewData.value = results
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
    message.error('预览刷新失败: ' + err.message)
  } finally {
    runningSql.value = false
  }
}

const handleSave = async () => {
  if (!formData.name || !formData.datasource_id || (!canvasTables.value.length && !formData.info.sql)) {
    return message.warning('请填写完整的必要信息')
  }
  
  saving.value = true
  const finalInfo = {
    ...formData.info,
    canvasTables: canvasTables.value,
    tableLinks: tableLinks.value,
    table_name: canvasTables.value.length > 0 ? canvasTables.value[0].name : undefined
  }
  
  if (formData.type === 'db_table') {
    finalInfo.sql = generateJoinSql()
  }

  const payload = {
    ...formData,
    info: finalInfo
  }

  try {
    if (route.params.id) {
      await updateDataset(route.params.id, payload)
      message.success('数据集更新成功')
    } else {
      await createDataset(payload)
      message.success('数据集创建成功')
    }
    router.push('/dataset/list')
  } catch (err) {
    message.error(err.message || '操作失败')
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
.header-left { display: flex; align-items: center; flex: 1; gap: 8px; }
.divider { margin: 0 4px; color: #d9d9d9; }
.dataset-name-input { font-size: 16px; font-weight: 500; width: 300px; }
.group-tag { margin-left: 8px; }

.editor-main { flex: 1; display: flex; overflow: hidden; }

.datasource-sidebar {
  width: 240px; background: #fff; border-right: 1px solid #d9d9d9; display: flex; flex-direction: column;
}
.sidebar-section { padding: 16px; border-bottom: 1px solid #f0f0f0; }
.section-title { font-size: 12px; font-weight: 500; color: #8c8c8c; margin-bottom: 8px; display: block; }
.section-header { display: flex; align-items: center; justify-content: space-between; }
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
  position: absolute; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; width: 160px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); 
  cursor: move; transition: border-color 0.2s, box-shadow 0.2s;
  z-index: 10;
}
.canvas-table-node:hover { border-color: #3b82f6; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
.canvas-table-node.active { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
.canvas-table-node.highlighted { border-color: #10b981; box-shadow: 0 0 12px rgba(16, 185, 129, 0.4); }

.node-header {
  padding: 10px 14px; background: #f8fafc; border-bottom: 1px solid #f1f5f9;
  border-radius: 8px 8px 0 0;
  display: flex; align-items: center; gap: 8px; font-size: 12px; color: #475569;
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
.bottom-header { 
  height: 40px; border-bottom: 1px solid #f0f0f0; padding: 0 16px; 
  display: flex; align-items: center; justify-content: space-between;
}
.bottom-tabs :deep(.ant-tabs-nav) { margin-bottom: 0; }
.bottom-body { flex: 1; overflow: hidden; display: flex; }

.metadata-container { flex: 1; display: flex; flex-direction: column; padding: 16px; overflow-y: auto; }
.meta-table-info { margin-bottom: 16px; }
.meta-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.meta-title-row h3 { margin: 0; }
.meta-alias { color: #8c8c8c; font-size: 14px; }
.meta-desc { color: #595959; margin: 0; }

.preview-container { flex: 1; overflow: hidden; padding: 16px; }
.empty-state { height: 100%; display: flex; align-items: center; justify-content: center; }

.join-config-container {
  flex: 1; overflow-y: auto; padding: 24px; background: #f8fafc;
}
.join-cards-grid {
  display: flex; flex-direction: column; gap: 20px; max-width: 1000px; margin: 0 auto;
}
.join-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); overflow: hidden; transition: all 0.3s;
}
.join-card:hover { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-color: #cbd5e1; }
.join-card-header {
  padding: 16px 24px; background: #f8fafc; border-bottom: 1px solid #f1f5f9;
  display: flex; align-items: center; justify-content: center; gap: 24px;
}
.table-tag-node {
  background: #fff; border: 1px solid #e2e8f0; padding: 6px 20px; border-radius: 20px;
  font-weight: 600; font-size: 13px; color: #334155; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.join-connector { display: flex; flex-direction: column; align-items: center; min-width: 120px; }
.join-type-label {
  font-size: 11px; font-weight: 700; color: #2563eb; background: #eff6ff;
  padding: 2px 10px; border-radius: 4px; margin-bottom: 6px; border: 1px solid #dbeafe;
}
.connector-line { height: 2px; width: 100%; background: #3b82f6; position: relative; }
.connector-line::after {
  content: ''; position: absolute; right: 0; top: 50%; transform: translateY(-50%);
  border: 4px solid transparent; border-left-color: #3b82f6;
}
.join-card-content { padding: 24px 32px; }
.input-label { font-size: 12px; color: #64748b; margin-bottom: 8px; font-weight: 500; }

.placeholder-content { display: flex; flex-direction: column; align-items: center; justify-content: center; }

:deep(.ant-table-thead > tr > th) { background: #fafafa; }
</style>
