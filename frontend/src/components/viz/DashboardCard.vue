<template>
  <div class="dashboard-card" @click="$emit('click')">
    <div class="card-cover">
      <div class="card-placeholder">
        <svg class="placeholder-icon" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
        <span class="placeholder-text">{{ dashboard.theme === 'dark' ? '深色大屏' : '浅色大屏' }}</span>
      </div>
      <a-tag
        :color="statusColor"
        class="card-status"
      >
        {{ statusLabel }}
      </a-tag>
    </div>
    <div class="card-body">
      <div class="card-name">{{ dashboard.name }}</div>
      <div class="card-desc" v-if="dashboard.description">{{ dashboard.description }}</div>
      <div class="card-meta">
        <span>{{ dashboard.auto_generated ? 'AI生成' : '手动创建' }}</span>
        <span class="card-date">更新于 {{ formatDate(dashboard.updated_at) }}</span>
      </div>
    </div>
    <div class="card-actions" @click.stop>
      <a-dropdown :trigger="['click']">
        <a-button type="text" size="small">
          <MoreOutlined />
        </a-button>
        <template #overlay>
          <a-menu @click="handleAction">
            <a-menu-item key="edit">
              <EditOutlined /> 编辑
            </a-menu-item>
            <a-menu-item key="view">
              <EyeOutlined /> 预览
            </a-menu-item>
            <a-menu-divider />
            <a-menu-item key="delete" danger>
              <DeleteOutlined /> 删除
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { MoreOutlined, EditOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  dashboard: { type: Object, required: true },
})

const emit = defineEmits(['click', 'edit', 'view', 'delete'])

const statusColor = computed(() => {
  const map = { draft: 'orange', published: 'green', archived: 'default' }
  return map[props.dashboard.status] || 'default'
})

const statusLabel = computed(() => {
  const map = { draft: '草稿', published: '已发布', archived: '已归档' }
  return map[props.dashboard.status] || '草稿'
})

function handleAction({ key }) {
  emit(key, props.dashboard.id)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.dashboard-card {
  position: relative;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-bg-surface);
}

.dashboard-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
  border-color: var(--color-primary);
}

.card-cover {
  position: relative;
  height: 140px;
  background: var(--color-sidebar-bg);
}

.card-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  color: var(--color-sidebar-text);
  margin-bottom: 8px;
}

.placeholder-text {
  font-size: 13px;
  color: var(--color-sidebar-text);
}

.card-status {
  position: absolute;
  top: 8px;
  right: 8px;
}

.card-body {
  padding: 16px;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.card-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.card-date {
  font-size: 11px;
}

.card-actions {
  position: absolute;
  top: 4px;
  right: 4px;
}
</style>