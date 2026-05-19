<template>
  <div class="datasource-list">
    <div class="page-header">
      <div class="page-title">
        <h2>数据源管理</h2>
        <p class="page-desc">管理数据仓库连接，支持 MySQL、PostgreSQL 等多种数据源类型</p>
      </div>
      <a-button type="primary" size="large" @click="showModal = true">
        <PlusOutlined /> 新增数据源
      </a-button>
    </div>

    <a-card class="table-card" :body-style="{ padding: 0 }">
      <a-table
        :columns="columns"
        :data-source="datasources"
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
            <a-tag color="blue">{{ record.type.toUpperCase() }}</a-tag>
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

    <a-modal
      v-model:open="showModal"
      title="新增数据源"
      @ok="handleCreate"
      :confirmLoading="creating"
      width="560px"
      destroyOnClose
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
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const loading = ref(false)
const datasources = ref([])
const showModal = ref(false)
const creating = ref(false)

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
  { title: '类型', key: 'type', width: 100, align: 'center' },
  { title: '连接信息', key: 'connection' },
  { title: '状态', key: 'status', width: 100, align: 'center' },
  { title: '操作', key: 'action', width: 180, align: 'center' }
]

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
      form.value = { name: '', type: 'mysql', host: '', port: 3306, database: '', username: '', password: '' }
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
  router.push(`/datasources/${id}`)
}

onMounted(fetchDatasources)
</script>

<style scoped>
.datasource-list {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f1f1f;
}

.page-desc {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}

.table-card {
  border-radius: 8px;
}

.datasource-table {
  padding: 0 16px;
}

.connection-info {
  color: #595959;
  font-size: 13px;
  font-family: monospace;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
}
</style>
