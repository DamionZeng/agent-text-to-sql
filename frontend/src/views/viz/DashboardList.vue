<template>
  <div class="dashboard-list-page">
    <div class="page-header">
      <div class="page-title">
        <h2>数据大屏</h2>
        <p class="page-desc">创建和管理数据可视化大屏，支持拖拽编排、多图表组合</p>
      </div>
      <a-space size="middle">
        <a-button @click="showAiGenerateModal">
          <RobotOutlined /> AI 创建大屏
        </a-button>
        <a-button type="primary" @click="showCreateModal = true">
          <PlusOutlined /> 新建大屏
        </a-button>
      </a-space>
    </div>

    <div class="filter-bar">
      <a-radio-group v-model:value="statusFilter" button-style="solid" size="small">
        <a-radio-button value="">全部</a-radio-button>
        <a-radio-button value="draft">草稿</a-radio-button>
        <a-radio-button value="published">已发布</a-radio-button>
        <a-radio-button value="archived">已归档</a-radio-button>
      </a-radio-group>
    </div>

    <a-spin :spinning="loading" v-if="dashboards.length > 0 || loading">
      <div class="dashboard-grid">
        <DashboardCard
          v-for="d in dashboards"
          :key="d.id"
          :dashboard="d"
          @click="goToEditor(d.id)"
          @edit="handleEdit(d.id)"
          @view="goToView(d.id)"
          @delete="handleDelete(d.id)"
        />
      </div>
      <div class="pagination-wrapper" v-if="total > pageSize">
        <a-pagination
          v-model:current="currentPage"
          :total="total"
          :page-size="pageSize"
          @change="onPageChange"
          show-less-items
        />
      </div>
    </a-spin>

    <a-empty v-else description="暂无数据大屏，点击上方按钮创建">
      <a-button type="primary" @click="showCreateModal = true">
        <PlusOutlined /> 新建大屏
      </a-button>
    </a-empty>

    <a-modal
      v-model:open="showCreateModal"
      title="新建大屏"
      @ok="handleCreate"
      :confirmLoading="creating"
      width="480px"
    >
      <a-form layout="vertical">
        <a-form-item label="大屏名称" required>
          <a-input v-model:value="createForm.name" placeholder="例如：电商运营看板" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="createForm.description" placeholder="简要描述（可选）" :rows="2" />
        </a-form-item>
        <a-form-item label="主题">
          <a-radio-group v-model:value="createForm.theme">
            <a-radio-button value="dark">深色</a-radio-button>
            <a-radio-button value="light">浅色</a-radio-button>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showAIModal"
      title="AI 创建大屏"
      width="520px"
      :footer="null"
    >
      <a-form layout="vertical">
        <a-form-item label="选择数据源" required>
          <a-select
            v-model:value="aiDatasourceId"
            placeholder="请选择数据源"
            :loading="loadingDatasources"
            style="width: 100%"
          >
            <a-select-option
              v-for="ds in datasources"
              :key="ds.id"
              :value="ds.id"
            >
              {{ ds.name || ds.host + '/' + ds.database }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述你的大屏需求">
          <a-textarea
            v-model:value="aiPrompt"
            placeholder="例如：做一个电商运营看板，包含总销售额、月趋势图、品类占比、Top10品类"
            :rows="4"
          />
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="showAIModal = false">取消</a-button>
          <a-button type="primary" @click="handleAICreate" style="margin-left: 8px" :disabled="!aiDatasourceId">
            开始生成
          </a-button>
        </div>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showRenameModal"
      title="编辑大屏信息"
      @ok="handleRename"
      :confirmLoading="renaming"
      width="400px"
    >
      <a-form layout="vertical">
        <a-form-item label="大屏名称" required>
          <a-input v-model:value="renameForm.name" placeholder="大屏名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="renameForm.description" placeholder="简要描述（可选）" :rows="2" />
        </a-form-item>
        <a-form-item label="主题">
          <a-radio-group v-model:value="renameForm.theme">
            <a-radio-button value="dark">深色</a-radio-button>
            <a-radio-button value="light">浅色</a-radio-button>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { useDashboard } from '../../composables/viz/useDashboard.js'
import DashboardCard from '../../components/viz/DashboardCard.vue'

const router = useRouter()
const { dashboards, total, loading, fetchList, createDashboard, deleteDashboard, updateDashboard } = useDashboard()

const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const showCreateModal = ref(false)
const showAIModal = ref(false)
const showRenameModal = ref(false)
const renaming = ref(false)
const renameForm = ref({ name: '', description: '', theme: 'dark' })
const renamingId = ref('')
const creating = ref(false)
const aiPrompt = ref('')
const aiDatasourceId = ref('')
const datasources = ref([])
const loadingDatasources = ref(false)

const createForm = ref({
  name: '',
  description: '',
  theme: 'dark',
})

onMounted(() => {
  loadList()
})

watch(statusFilter, () => {
  currentPage.value = 1
  loadList()
})

async function loadDatasources() {
  loadingDatasources.value = true
  try {
    const res = await fetch('/api/metadata/datasources')
    if (res.ok) {
      const data = await res.json()
      datasources.value = data.items || data || []
      if (datasources.value.length > 0) {
        aiDatasourceId.value = datasources.value[0].id
      }
    }
  } catch (e) {
    console.error('加载数据源失败', e)
  } finally {
    loadingDatasources.value = false
  }
}

function loadList() {
  fetchList((currentPage.value - 1) * pageSize.value, pageSize.value, statusFilter.value || null)
}

function onPageChange(page) {
  currentPage.value = page
  loadList()
}

async function handleCreate() {
  if (!createForm.value.name.trim()) return
  creating.value = true
  try {
    const result = await createDashboard(createForm.value)
    showCreateModal.value = false
    createForm.value = { name: '', description: '', theme: 'dark' }
    router.push(`/viz/dashboards/${result.id}/edit`)
  } finally {
    creating.value = false
  }
}

function handleAICreate() {
  if (!aiPrompt.value.trim() || !aiDatasourceId.value) return
  showAIModal.value = false
  router.push({
    path: '/viz/dashboards/new/edit',
    query: { ai: 'true', prompt: aiPrompt.value, datasourceId: aiDatasourceId.value },
  })
}

function showAiGenerateModal() {
  aiPrompt.value = ''
  aiDatasourceId.value = datasources.value.length > 0 ? datasources.value[0].id : ''
  loadDatasources()
  showAIModal.value = true
}

function handleEdit(id) {
  const d = dashboards.value.find((item) => item.id === id)
  if (!d) return
  renamingId.value = id
  renameForm.value = {
    name: d.name || '',
    description: d.description || '',
    theme: d.theme || 'dark',
  }
  showRenameModal.value = true
}

async function handleRename() {
  if (!renameForm.value.name.trim()) return
  renaming.value = true
  try {
    await updateDashboard(renamingId.value, {
      name: renameForm.value.name.trim(),
      description: renameForm.value.description.trim(),
      theme: renameForm.value.theme,
    })
    showRenameModal.value = false
    loadList()
  } finally {
    renaming.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteDashboard(id)
    loadList()
  } catch (e) {
    console.error(e)
  }
}

function goToEditor(id) {
  router.push(`/viz/dashboards/${id}/edit`)
}

function goToView(id) {
  router.push(`/viz/dashboards/${id}/view`)
}
</script>

<style scoped>
.dashboard-list-page {
  max-width: 1200px;
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

.filter-bar {
  margin-bottom: 20px;
}

.filter-bar :deep(.ant-radio-button-wrapper) {
  border-color: var(--color-border-light);
  color: var(--color-text-secondary);
}

.filter-bar :deep(.ant-radio-button-wrapper-checked) {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1400px) {
  .dashboard-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 1000px) {
  .dashboard-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .dashboard-grid { grid-template-columns: 1fr; }
}
</style>