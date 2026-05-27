<template>
  <div class="datasource-list-container">
    <div class="page-header">
      <div class="page-title">
        <h2>数据源管理</h2>
        <p class="page-desc">管理数据仓库连接，支持 MySQL、PostgreSQL 等多种数据源类型</p>
      </div>
      <a-button type="primary" size="large" @click="openCreateModal">
        <PlusOutlined /> 新增数据源
      </a-button>
    </div>

    <div class="main-layout">
      <!-- Left Sidebar: Types/Groups -->
      <div class="list-sidebar">
        <a-card class="sidebar-card" :bordered="false">
          <div class="sidebar-header">
            <span class="title">数据源类型</span>
          </div>
          <div class="group-list">
            <div 
              class="group-item" 
              :class="{ active: activeType === 'all' }"
              @click="activeType = 'all'"
            >
              <DatabaseOutlined />
              <span class="name">全部类型</span>
              <span class="count">{{ datasources.length }}</span>
            </div>
            <div 
              class="group-item"
              :class="{ active: activeType === 'mysql' }"
              @click="activeType = 'mysql'"
            >
              <div class="db-icon mysql"></div>
              <span class="name">MySQL</span>
              <span class="count">{{ datasources.filter(d => d.type === 'mysql').length }}</span>
            </div>
            <div 
              class="group-item"
              :class="{ active: activeType === 'postgresql' }"
              @click="activeType = 'postgresql'"
            >
              <div class="db-icon postgresql"></div>
              <span class="name">PostgreSQL</span>
              <span class="count">{{ datasources.filter(d => d.type === 'postgresql').length }}</span>
            </div>
          </div>
        </a-card>
      </div>

      <!-- Right Content: Datasource Table -->
      <div class="list-content">
        <a-card class="table-card" :body-style="{ padding: 0 }" :bordered="false">
          <a-table
            :columns="columns"
            :data-source="filteredDatasources"
            :loading="loading"
            row-key="id"
            :pagination="{ pageSize: 10 }"
            class="datasource-table"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-badge
                  :status="record.status === 'active' ? 'success' : 'default'"
                  :text="record.status === 'active' ? '正常' : '未激活'"
                />
              </template>
              <template v-if="column.key === 'connection'">
                <span class="connection-info">{{ record.host }}:{{ record.port }} / {{ record.database }}</span>
              </template>
              <template v-if="column.key === 'type'">
                <div class="type-cell">
                  <div :class="['db-icon-small', record.type]"></div>
                  <span>{{ record.type.toUpperCase() }}</span>
                </div>
              </template>
              <template v-if="column.key === 'action'">
                <a-space size="middle">
                  <a-button type="primary" ghost size="small" @click="goToDetail(record.id)">
                    管理
                  </a-button>
                  <a-popconfirm
                    title="确认删除该数据源？"
                    ok-text="删除"
                    cancel-text="取消"
                    @confirm="handleDelete(record.id)"
                  >
                    <a-button danger size="small">删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </div>
    </div>

    <a-modal
      v-model:open="showModal"
      title="新增数据源"
      @ok="handleCreate"
      :confirmLoading="creating"
      width="560px"
      destroyOnClose
      :footer="null"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="数据源名称" required>
              <a-input v-model:value="form.name" placeholder="例如：生产环境 MySQL" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="数据库类型" required>
              <a-select v-model:value="form.type" placeholder="请选择">
                <a-select-option value="mysql">MySQL</a-select-option>
                <a-select-option value="postgresql">PostgreSQL</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="主机地址" required>
              <a-input v-model:value="form.host" placeholder="例如：localhost 或 IP 地址" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="端口" required>
              <a-input-number v-model:value="form.port" :min="1" :max="65535" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="数据库名" required>
          <a-input v-model:value="form.database" placeholder="请输入数据库名称" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用户名" required>
              <a-input v-model:value="form.username" placeholder="用户名" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="密码" required>
              <a-input-password v-model:value="form.password" placeholder="密码" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-alert
            v-if="testResult"
            :message="testResult.message"
            :type="testResult.success ? 'success' : 'error'"
            show-icon
            closable
            @close="testResult = null"
            style="margin-bottom: 12px"
          />
          <a-space style="width: 100%; justify-content: flex-end;">
            <a-button @click="showModal = false">取消</a-button>
            <a-button @click="handleTest" :loading="testing">测试连接</a-button>
            <a-button type="primary" @click="handleCreate" :loading="creating">创建</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, DatabaseOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const loading = ref(false)
const datasources = ref([])
const activeType = ref('all')
const showModal = ref(false)
const creating = ref(false)
const testing = ref(false)
const testResult = ref(null)

const form = ref({
  name: '',
  type: 'mysql',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: ''
})

const columns = [
  { title: '数据源名称', dataIndex: 'name', key: 'name', width: 200 },
  { title: '类型', key: 'type', width: 140, align: 'center' },
  { title: '连接信息', key: 'connection' },
  { title: '状态', key: 'status', width: 100, align: 'center' },
  { title: '操作', key: 'action', width: 180, align: 'center' }
]

const filteredDatasources = computed(() => {
  if (activeType.value === 'all') return datasources.value
  return datasources.value.filter(d => d.type === activeType.value)
})

const fetchDatasources = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/metadata/datasources')
    const data = await res.json()
    datasources.value = data
  } catch (e) {
    message.error('获取数据源列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  // Requirement 1: Context-aware creation
  form.value = {
    name: '',
    type: activeType.value !== 'all' ? activeType.value : 'mysql',
    host: '',
    port: activeType.value === 'postgresql' ? 5432 : 3306,
    database: '',
    username: '',
    password: ''
  }
  showModal.value = true
}

const handleCreate = async () => {
  if (!form.value.name || !form.value.host || !form.value.database || !form.value.username || !form.value.password) {
    message.warning('请填写完整信息')
    return
  }
  creating.value = true
  try {
    const res = await fetch('/api/metadata/datasources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (res.ok) {
      message.success('创建成功')
      showModal.value = false
      fetchDatasources()
    } else {
      message.error('创建失败')
    }
  } catch (e) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

const handleDelete = async (id) => {
  try {
    const res = await fetch(`/api/metadata/datasources/${id}`, { method: 'DELETE' })
    if (res.ok) {
      message.success('删除成功')
      fetchDatasources()
    } else {
      message.error('删除失败')
    }
  } catch (e) {
    message.error('删除失败')
  }
}

const goToDetail = (id) => {
  router.push(`/metadata/datasources/${id}`)
}

const handleTest = async () => {
  if (!form.value.name || !form.value.host || !form.value.database || !form.value.username || !form.value.password) {
    message.warning('请填写完整信息后再测试')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const res = await fetch('/api/metadata/datasources/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    const data = await res.json()
    testResult.value = data
  } catch (e) {
    testResult.value = { success: false, message: '测试请求失败' }
  } finally {
    testing.value = false
  }
}

onMounted(fetchDatasources)
</script>

<style scoped>
.datasource-list-container {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.page-desc {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.main-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.list-sidebar {
  width: 260px;
  flex-shrink: 0;
}

.sidebar-card {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  min-height: 600px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.sidebar-header .title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.group-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-text-secondary);
}

.group-item:hover {
  background: var(--color-secondary-light);
}

.group-item.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
}

.group-item .name {
  flex: 1;
  font-size: 13px;
}

.group-item .count {
  font-size: 11px;
  background: rgba(0,0,0,0.05);
  padding: 1px 6px;
  border-radius: 10px;
  color: var(--color-text-tertiary);
}

.group-item.active .count {
  background: rgba(79, 70, 229, 0.1);
  color: var(--color-primary);
}

/* Database Icons */
.db-icon {
  width: 18px;
  height: 18px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}
.db-icon.mysql {
  background-image: url('https://img.icons8.com/color/48/000000/mysql-logo.png');
}
.db-icon.postgresql {
  background-image: url('https://img.icons8.com/color/48/000000/postgreesql.png');
}

.db-icon-small {
  width: 14px;
  height: 14px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  display: inline-block;
  margin-right: 6px;
}
.db-icon-small.mysql {
  background-image: url('https://img.icons8.com/color/48/000000/mysql-logo.png');
}
.db-icon-small.postgresql {
  background-image: url('https://img.icons8.com/color/48/000000/postgreesql.png');
}

.type-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-content {
  flex: 1;
  min-width: 0;
}

.table-card {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.table-card :deep(.ant-card-body) {
  padding: 0;
}

.datasource-table :deep(.ant-table-thead > tr > th) {
  background: var(--color-bg-page);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.datasource-table :deep(.ant-table-tbody > tr:hover > td) {
  background: var(--color-primary-light);
}

.connection-info {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
