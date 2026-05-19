<template>
  <div v-if="datasource" class="datasource-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-title-section">
        <a-button type="link" @click="$router.back()" class="back-btn">
          <LeftOutlined /> 返回
        </a-button>
        <div class="title-wrapper">
          <h2>{{ datasource.name }}</h2>
          <a-tag :color="datasource.status === 'active' ? 'green' : 'default'" class="status-tag">
            {{ datasource.status === 'active' ? '正常' : '未激活' }}
          </a-tag>
        </div>
        <p class="connection-desc">
          {{ datasource.type.toUpperCase() }} · {{ datasource.host }}:{{ datasource.port }} / {{ datasource.database }}
        </p>
      </div>
      <a-space>
        <a-button @click="testConnection" :loading="testing">测试连接</a-button>
        <a-button type="primary" @click="startSync" :loading="syncing">
          <SyncOutlined /> AI 初始化/同步
        </a-button>
      </a-space>
    </div>

    <!-- 同步状态 -->
    <a-alert
      v-if="syncStatus"
      :message="syncStatus.message"
      :type="syncStatus.type"
      show-icon
      style="margin-bottom: 20px"
      closable
      @close="syncStatus = null"
    />

    <!-- 元数据编辑器 -->
    <a-card v-if="metaConfig" class="editor-card" :bordered="false">
      <template #title>
        <div class="card-title">
          <span>元数据编辑器</span>
          <a-space>
            <a-button @click="saveDraft" :loading="saving">保存草稿</a-button>
            <a-button type="primary" @click="publish" :loading="publishing">发布同步</a-button>
          </a-space>
        </div>
      </template>

      <a-tabs v-model:activeKey="activeTab" class="meta-tabs">
        <!-- 表管理 Tab -->
        <a-tab-pane key="tables" tab="表管理">
          <div class="table-list">
            <a-collapse v-model:activeKey="expandedTables" accordion>
              <a-collapse-panel
                v-for="table in metaConfig.tables"
                :key="table.name"
                :header="tableHeader(table)"
              >
                <div class="table-edit-section">
                  <a-row :gutter="16" class="table-meta-row">
                    <a-col :span="8">
                      <a-form-item label="表角色">
                        <a-select v-model:value="table.role" style="width: 100%">
                          <a-select-option value="dim">维度表</a-select-option>
                          <a-select-option value="fact">事实表</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                    <a-col :span="16">
                      <a-form-item label="表描述">
                        <a-input v-model:value="table.description" placeholder="请输入表描述" />
                      </a-form-item>
                    </a-col>
                  </a-row>

                  <a-divider style="margin: 12px 0" />

                  <h4 class="section-subtitle">字段列表</h4>
                  <a-table
                    :columns="columnColumns"
                    :data-source="table.columns"
                    row-key="name"
                    size="small"
                    :pagination="false"
                    bordered
                  >
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.key === 'role'">
                        <a-select v-model:value="record.role" size="small" style="width: 110px">
                          <a-select-option value="primary_key">主键</a-select-option>
                          <a-select-option value="foreign_key">外键</a-select-option>
                          <a-select-option value="measure">度量</a-select-option>
                          <a-select-option value="dimension">维度</a-select-option>
                        </a-select>
                      </template>
                      <template v-if="column.key === 'description'">
                        <a-input v-model:value="record.description" size="small" placeholder="字段描述" />
                      </template>
                      <template v-if="column.key === 'alias'">
                        <a-input
                          v-model:value="record.aliasStr"
                          size="small"
                          placeholder="用逗号分隔"
                          @blur="updateAlias(record)"
                        />
                      </template>
                      <template v-if="column.key === 'sync'">
                        <a-switch v-model:checked="record.sync" size="small" />
                      </template>
                    </template>
                  </a-table>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </a-tab-pane>

        <!-- 指标管理 Tab -->
        <a-tab-pane key="metrics" tab="指标管理">
          <a-table
            :columns="metricColumns"
            :data-source="metaConfig.metrics"
            row-key="name"
            bordered
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'description'">
                <a-input v-model:value="record.description" placeholder="指标描述" />
              </template>
              <template v-if="column.key === 'relevant_columns'">
                <a-select
                  v-model:value="record.relevant_columns"
                  mode="multiple"
                  style="width: 100%"
                  placeholder="选择关联字段"
                  :options="allColumnOptions"
                />
              </template>
              <template v-if="column.key === 'alias'">
                <a-input
                  v-model:value="record.aliasStr"
                  placeholder="用逗号分隔"
                  @blur="updateAlias(record)"
                />
              </template>
              <template v-if="column.key === 'action'">
                <a-button type="link" danger @click="removeMetric(record.name)">删除</a-button>
              </template>
            </template>
          </a-table>

          <a-button type="dashed" block style="margin-top: 16px" @click="addMetric">
            <PlusOutlined /> 新增指标
          </a-button>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 空状态 -->
    <a-card v-else class="empty-card">
      <a-empty description="暂无元数据">
        <template #extra>
          <a-button type="primary" @click="startSync">
            <SyncOutlined /> 点击 AI 初始化
          </a-button>
        </template>
      </a-empty>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { SyncOutlined, LeftOutlined, PlusOutlined } from '@ant-design/icons-vue'

const route = useRoute()
const datasourceId = route.params.id

const datasource = ref(null)
const metaConfig = ref(null)
const activeTab = ref('tables')
const expandedTables = ref([])
const syncing = ref(false)
const saving = ref(false)
const publishing = ref(false)
const testing = ref(false)
const syncStatus = ref(null)

const columnColumns = [
  { title: '字段名', dataIndex: 'name', key: 'name', width: 140 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '角色', key: 'role', width: 130 },
  { title: '描述', key: 'description' },
  { title: '别名', key: 'alias', width: 180 },
  { title: '同步ES', key: 'sync', width: 80, align: 'center' }
]

const metricColumns = [
  { title: '指标名', dataIndex: 'name', key: 'name', width: 150 },
  { title: '描述', key: 'description' },
  { title: '关联字段', key: 'relevant_columns', width: 250 },
  { title: '别名', key: 'alias', width: 180 },
  { title: '操作', key: 'action', width: 80, align: 'center' }
]

const allColumnOptions = computed(() => {
  if (!metaConfig.value?.tables) return []
  const options = []
  metaConfig.value.tables.forEach(table => {
    table.columns.forEach(col => {
      options.push({
        label: `${table.name}.${col.name}`,
        value: `${table.name}.${col.name}`
      })
    })
  })
  return options
})

const tableHeader = (table) => {
  const roleText = table.role === 'dim' ? '维度表' : table.role === 'fact' ? '事实表' : '未知'
  return `${table.name} (${roleText}) - ${table.description || '无描述'}`
}

const fetchDatasource = async () => {
  try {
    const res = await fetch(`/api/metadata/datasources/${datasourceId}`)
    datasource.value = await res.json()
  } catch (e) {
    message.error('获取数据源详情失败')
  }
}

const fetchDraft = async () => {
  try {
    const res = await fetch(`/api/metadata/datasources/${datasourceId}/draft`)
    if (res.ok) {
      const draft = await res.json()
      metaConfig.value = draft.config_json
      initAliasStr()
    }
  } catch (e) {
    // 无草稿时忽略
  }
}

const initAliasStr = () => {
  if (!metaConfig.value) return
  metaConfig.value.tables?.forEach(table => {
    table.columns?.forEach(col => {
      if (col.alias && Array.isArray(col.alias)) {
        col.aliasStr = col.alias.join(', ')
      } else {
        col.aliasStr = ''
      }
    })
  })
  metaConfig.value.metrics?.forEach(metric => {
    if (metric.alias && Array.isArray(metric.alias)) {
      metric.aliasStr = metric.alias.join(', ')
    } else {
      metric.aliasStr = ''
    }
  })
}

const updateAlias = (record) => {
  record.alias = record.aliasStr
    ? record.aliasStr.split(/[,，]/).map(s => s.trim()).filter(Boolean)
    : []
}

const testConnection = async () => {
  testing.value = true
  try {
    const res = await fetch(`/api/metadata/datasources/${datasourceId}/test`, { method: 'POST' })
    if (res.ok) {
      message.success('连接成功')
    } else {
      message.error('连接失败')
    }
  } catch (e) {
    message.error('连接失败')
  } finally {
    testing.value = false
  }
}

const startSync = async () => {
  syncing.value = true
  syncStatus.value = { type: 'info', message: 'AI 同步任务启动中...' }

  try {
    const eventSource = new EventSource(`/api/metadata/datasources/${datasourceId}/sync`)
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'progress') {
        syncStatus.value = { type: 'info', message: `${data.step}: ${data.message}` }
      } else if (data.type === 'result') {
        syncStatus.value = { type: 'success', message: '同步完成' }
        metaConfig.value = data.data.meta_config
        initAliasStr()
        eventSource.close()
        syncing.value = false
      } else if (data.type === 'error') {
        syncStatus.value = { type: 'error', message: data.message }
        eventSource.close()
        syncing.value = false
      }
    }
    eventSource.onerror = () => {
      syncStatus.value = { type: 'error', message: '同步连接异常' }
      eventSource.close()
      syncing.value = false
    }
  } catch (e) {
    message.error('启动同步失败')
    syncing.value = false
  }
}

const saveDraft = async () => {
  saving.value = true
  try {
    const res = await fetch(`/api/metadata/datasources/${datasourceId}/draft`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config_json: metaConfig.value })
    })
    if (res.ok) {
      message.success('草稿保存成功')
    } else {
      message.error('保存失败')
    }
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const publish = async () => {
  publishing.value = true
  try {
    const res = await fetch(`/api/metadata/datasources/${datasourceId}/publish`, { method: 'POST' })
    if (res.ok) {
      message.success('发布成功')
    } else {
      message.error('发布失败')
    }
  } catch (e) {
    message.error('发布失败')
  } finally {
    publishing.value = false
  }
}

const addMetric = () => {
  if (!metaConfig.value.metrics) {
    metaConfig.value.metrics = []
  }
  metaConfig.value.metrics.push({
    name: '新指标',
    description: '',
    relevant_columns: [],
    alias: [],
    aliasStr: ''
  })
}

const removeMetric = (name) => {
  const idx = metaConfig.value.metrics.findIndex(m => m.name === name)
  if (idx > -1) {
    metaConfig.value.metrics.splice(idx, 1)
  }
}

onMounted(() => {
  fetchDatasource()
  fetchDraft()
})
</script>

<style scoped>
.datasource-detail {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.page-title-section {
  flex: 1;
}

.back-btn {
  padding-left: 0;
  margin-bottom: 8px;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-wrapper h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f1f1f;
}

.status-tag {
  font-size: 12px;
}

.connection-desc {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
  font-family: monospace;
}

.editor-card {
  border-radius: 8px;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.meta-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}

.table-list {
  background: #fafafa;
  border-radius: 8px;
  padding: 8px;
}

.table-meta-row {
  background: #fff;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.section-subtitle {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.empty-card {
  border-radius: 8px;
  padding: 60px 0;
}
</style>
