<template>
  <div class="dataset-list-container">
    <div class="page-header">
      <div class="page-title">
        <h2>数据集管理</h2>
        <p class="page-desc">构建和管理用于数据可视化的大屏数据集定义</p>
      </div>
      <a-button type="primary" size="large" @click="goToCreate">
        <PlusOutlined /> 新增数据集
      </a-button>
    </div>

    <div class="main-layout">
      <!-- Left Sidebar: Folders/Groups -->
      <div class="list-sidebar">
        <a-card class="sidebar-card" :bordered="false">
          <div class="sidebar-header">
            <span class="title">所有分组</span>
            <a-button type="text" size="small" @click="showGroupModal = true"><PlusOutlined /></a-button>
          </div>
          <div class="search-box">
            <a-input v-model:value="groupSearch" placeholder="搜索分组" size="small">
              <template #prefix><SearchOutlined style="color: #bfbfbf" /></template>
            </a-input>
          </div>
          <div class="group-list">
            <div 
              class="group-item" 
              :class="{ active: activeGroup === 'all' }"
              @click="onGroupSelect('all')"
            >
              <FolderOutlined />
              <span class="name">全部数据集</span>
              <span class="count">{{ totalDatasetCount }}</span>
            </div>
            
            <div 
              class="group-item" 
              :class="{ active: activeGroup === 'default' }"
              @click="onGroupSelect('default')"
            >
              <FolderOutlined />
              <span class="name">默认分组</span>
              <span class="count">{{ defaultGroupCount }}</span>
            </div>

            <div 
              v-for="group in filteredGroups" 
              :key="group.id" 
              class="group-item"
              :class="{ active: activeGroup === group.id }"
              @click="onGroupSelect(group.id)"
            >
              <FolderOutlined />
              <span class="name">{{ group.name }}</span>
              <div class="group-actions">
                <a-popconfirm title="确定删除该分组吗？" @confirm="handleDeleteGroup(group.id)">
                  <DeleteOutlined class="del-icon" @click.stop />
                </a-popconfirm>
              </div>
            </div>
          </div>
        </a-card>
      </div>

      <!-- Right Content: Dataset Table -->
      <div class="list-content">
        <a-card class="table-card" :body-style="{ padding: 0 }" :bordered="false">
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
    </div>

    <!-- Create Group Modal -->
    <a-modal
      v-model:open="showGroupModal"
      title="新建分组"
      @ok="handleCreateGroup"
      :confirmLoading="creatingGroup"
      width="400px"
    >
      <a-form layout="vertical">
        <a-form-item label="分组名称" required>
          <a-input v-model:value="newGroupName" placeholder="请输入分组名称" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, SearchOutlined, FolderOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { useDataset } from '../../composables/dataset/useDataset'
import { message } from 'ant-design-vue'

const router = useRouter()
const { datasets, loading, fetchList, deleteDataset, fetchGroups, createGroup, deleteGroup } = useDataset()

const groupSearch = ref('')
const groups = ref([])
const activeGroup = ref('all')
const showGroupModal = ref(false)
const creatingGroup = ref(false)
const newGroupName = ref('')

const totalDatasetCount = ref(0)
const defaultGroupCount = ref(0)

const columns = [
  { title: '数据集名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type', width: 120, align: 'center' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120, align: 'center' },
  { title: '操作', key: 'action', width: 180, align: 'center' }
]

const filteredGroups = computed(() => {
  if (!groupSearch.value) return groups.value
  return groups.value.filter(g => g.name.toLowerCase().includes(groupSearch.value.toLowerCase()))
})

const loadData = async () => {
  // Fetch groups
  try {
    groups.value = await fetchGroups()
  } catch (e) {
    message.error('加载分组失败')
  }

  // Fetch datasets for active group
  await fetchList(activeGroup.value === 'all' ? null : activeGroup.value)
  
  // Update counts (mock logic for now, in production we might need a dedicated count API)
  if (activeGroup.value === 'all') {
    totalDatasetCount.value = datasets.value.length
    defaultGroupCount.value = datasets.value.filter(d => !d.group_id).length
  }
}

const onGroupSelect = async (groupId) => {
  activeGroup.value = groupId
  await fetchList(groupId === 'all' ? null : groupId)
}

onMounted(loadData)

const handleCreateGroup = async () => {
  if (!newGroupName.value.trim()) return message.warning('请输入分组名称')
  creatingGroup.value = true
  try {
    await createGroup(newGroupName.value.trim())
    message.success('创建成功')
    showGroupModal.value = false
    newGroupName.value = ''
    await loadData()
  } catch (e) {
    message.error('创建失败')
  } finally {
    creatingGroup.value = false
  }
}

const handleDeleteGroup = async (id) => {
  try {
    await deleteGroup(id)
    message.success('删除成功')
    if (activeGroup.value === id) activeGroup.value = 'all'
    await loadData()
  } catch (e) {
    message.error('删除失败')
  }
}

const goToCreate = () => {
  // Requirement 4: Context-aware creation
  const query = {}
  if (activeGroup.value !== 'all' && activeGroup.value !== 'default') {
    query.group_id = activeGroup.value
  }
  router.push({ path: '/dataset/create', query })
}

const goToEdit = (id) => {
  router.push(`/dataset/edit/${id}`)
}

const handleDelete = async (id) => {
  try {
    await deleteDataset(id)
    message.success('删除成功')
    await fetchList(activeGroup.value === 'all' ? null : activeGroup.value)
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.dataset-list-container {
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

/* Sidebar Styles */
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
}

.sidebar-header .title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.search-box {
  margin-bottom: 16px;
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
  position: relative;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.group-actions {
  display: none;
}

.group-item:hover .group-actions {
  display: block;
}

.del-icon {
  font-size: 12px;
  color: #ff4d4f;
  margin-left: 4px;
}

/* Content Styles */
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

.dataset-table :deep(.ant-table-thead > tr > th) {
  background: var(--color-bg-page);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.dataset-table :deep(.ant-table-tbody > tr:hover > td) {
  background: var(--color-primary-light);
}

.dataset-table :deep(.ant-table-tbody > tr:last-child > td) {
  border-bottom: none;
}
</style>
