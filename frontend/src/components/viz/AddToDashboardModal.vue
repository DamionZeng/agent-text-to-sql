<template>
  <a-modal
    v-model:open="visible"
    title="加入大屏"
    width="480px"
    @ok="handleConfirm"
    :confirmLoading="loading"
  >
    <div class="add-to-dashboard-modal">
      <a-radio-group v-model:value="mode" style="width: 100%; margin-bottom: 16px">
        <a-radio-button value="existing" style="width: 50%; text-align: center">
          选择已有大屏
        </a-radio-button>
        <a-radio-button value="new" style="width: 50%; text-align: center">
          创建新大屏
        </a-radio-button>
      </a-radio-group>

      <template v-if="mode === 'existing'">
        <div class="dashboard-list" v-if="dashboards.length > 0">
          <div
            v-for="d in dashboards"
            :key="d.id"
            class="dashboard-option"
            :class="{ selected: selectedDashboardId === d.id }"
            @click="selectedDashboardId = d.id"
          >
            <span class="option-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
              </svg>
            </span>
            <div class="option-info">
              <span class="option-name">{{ d.name }}</span>
              <span class="option-status">{{ statusLabel(d.status) }}</span>
            </div>
          </div>
        </div>
        <a-empty v-else description="暂无可用大屏" />
      </template>

      <template v-if="mode === 'new'">
        <a-form layout="vertical">
          <a-form-item label="大屏名称" required>
            <a-input v-model:value="newDashboardName" placeholder="例如：销售数据看板" />
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea v-model:value="newDashboardDesc" placeholder="简要描述（可选）" :rows="2" />
          </a-form-item>
        </a-form>
      </template>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  dashboards: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'confirm'])

const visible = ref(props.open)
const mode = ref('existing')
const selectedDashboardId = ref(null)
const newDashboardName = ref('')
const newDashboardDesc = ref('')

watch(
  () => props.open,
  (val) => {
    visible.value = val
  }
)

watch(visible, (val) => {
  emit('update:open', val)
})

function statusLabel(status) {
  const map = { draft: '草稿', published: '已发布', archived: '已归档' }
  return map[status] || '草稿'
}

function handleConfirm() {
  if (mode.value === 'existing' && selectedDashboardId.value) {
    emit('confirm', { type: 'existing', dashboardId: selectedDashboardId.value })
  } else if (mode.value === 'new' && newDashboardName.value.trim()) {
    emit('confirm', {
      type: 'new',
      name: newDashboardName.value.trim(),
      description: newDashboardDesc.value.trim(),
    })
  }
  visible.value = false
}
</script>

<style scoped>
.add-to-dashboard-modal {
  min-height: 200px;
}

.dashboard-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.dashboard-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
}

.dashboard-option:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.dashboard-option.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.option-icon {
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.option-info {
  display: flex;
  flex-direction: column;
}

.option-name {
  font-size: 14px;
  font-weight: 500;
}

.option-status {
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>