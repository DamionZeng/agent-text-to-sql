<template>
  <div class="dataset-list">
    <div class="page-header">
      <div class="page-title">
        <h2>数据集管理</h2>
        <p class="page-desc">构建和管理用于数据可视化的大屏数据集定义</p>
      </div>
      <a-button type="primary" size="large" @click="goToCreate">
        <PlusOutlined /> 新增数据集
      </a-button>
    </div>

    <a-card class="table-card" :body-style="{ padding: 0 }">
      <a-table
        :columns="columns"
        :data-source="datasets"
        :loading="loading"
        row-key="id"
        :pagination="{ pageSize: 10 }"
        class="dataset-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="record.type === 'db_table' ? 'blue' : 'green'">
              {{ record.type === 'db_table' ? '物理表' : '自定义SQL' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.status === 'active' ? 'success' : 'default'"
              :text="record.status === 'active' ? '正常' : '已停用'"
            />
          </template>
          <template v-if="column.key === 'action'">
            <a-space size="middle">
              <a-button type="primary" ghost size="small" @click="goToEdit(record.id)">
                编辑
              </a-button>
              <a-popconfirm title="确定要删除该数据集吗？" @confirm="handleDelete(record.id)">
                <a-button type="link" danger size="small">
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useDataset } from '../../composables/dataset/useDataset'

const router = useRouter()
const { datasets, loading, fetchList, deleteDataset } = useDataset()

const columns = [
  { title: '数据集名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', width: 200 }
]

onMounted(async () => {
  await fetchList()
})

const goToCreate = () => {
  router.push('/dataset/create')
}

const goToEdit = (id) => {
  router.push(`/dataset/edit/${id}`)
}

const handleDelete = async (id) => {
  try {
    await deleteDataset(id)
    await fetchList()
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.dataset-list {
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.page-title h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}
.page-desc {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}
.table-card {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}
</style>
