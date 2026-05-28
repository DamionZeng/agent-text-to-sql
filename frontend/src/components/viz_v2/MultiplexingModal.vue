<template>
  <a-modal
    v-model:open="visible"
    title="跨仪表板复用组件"
    width="600px"
    @ok="handleConfirm"
    :confirm-loading="loading"
  >
    <div class="multiplexing-modal">
      <a-input-search
        v-model:value="searchQuery"
        placeholder="搜索仪表板或图表名称..."
        style="margin-bottom: 16px"
      />
      <div class="dashboard-tree" v-if="dashboards.length > 0">
        <div
          v-for="db in filteredDashboards"
          :key="db.id"
          class="db-group"
        >
          <div class="db-header" @click="toggleExpand(db.id)">
            <span class="db-toggle">{{ expandedIds.has(db.id) ? '▼' : '▶' }}</span>
            <span class="db-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
              </svg>
            </span>
            <span class="db-name">{{ db.name }}</span>
            <span class="db-status-tag">{{ db.status === 'published' ? '已发布' : '草稿' }}</span>
          </div>
          <div class="panel-list" v-if="expandedIds.has(db.id)">
            <div
              v-for="panel in (db.panels || [])"
              :key="panel.id"
              class="panel-item"
              :class="{ selected: selectedPanelId === panel.id }"
              @click="selectedPanelId = panel.id; selectedDashboardId = db.id"
            >
              <span class="panel-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>
                </svg>
              </span>
              <span class="panel-name">{{ panel.title || '未命名面板' }}</span>
              <span class="panel-type">{{ panel.chart_type || 'bar' }}</span>
            </div>
            <div v-if="!(db.panels || []).length" class="panel-empty">该仪表板暂无组件</div>
          </div>
        </div>
      </div>
      <a-empty v-else description="暂无可用仪表板" />
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'confirm'])

const visible = ref(false)
const loading = ref(false)
const dashboards = ref([])
const searchQuery = ref('')
const expandedIds = ref(new Set())
const selectedDashboardId = ref(null)
const selectedPanelId = ref(null)

const filteredDashboards = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return dashboards.value
  return dashboards.value.filter(db => {
    if (db.name.toLowerCase().includes(q)) return true
    return (db.panels || []).some(p => p.title && p.title.toLowerCase().includes(q))
  })
})

watch(() => props.open, async (val) => {
  visible.value = val
  if (val) {
    await loadDashboards()
  }
})

watch(visible, (val) => { emit('update:open', val) })

async function loadDashboards() {
  loading.value = true
  try {
    const res = await fetch('/api/viz/dashboards?limit=50')
    if (!res.ok) throw new Error('加载失败')
    const data = await res.json()
    dashboards.value = (data.items || data || []).filter(d => d.id)
    for (const db of dashboards.value) {
      if (!db.panels) {
        try {
          const r2 = await fetch(`/api/viz/dashboards/` + db.id)
          if (r2.ok) {
            const d2 = await r2.json()
            db.panels = d2.panels || []
          }
        } catch (_) { db.panels = [] }
      }
    }
  } catch (e) {
    console.error('加载仪表板列表失败', e)
    dashboards.value = []
  } finally {
    loading.value = false
  }
}

function toggleExpand(id) {
  const s = new Set(expandedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedIds.value = s
}

function handleConfirm() {
  if (selectedPanelId.value && selectedDashboardId.value) {
    emit('confirm', {
      dashboardId: selectedDashboardId.value,
      panelId: selectedPanelId.value,
    })
  }
  visible.value = false
}
</script>

<style scoped>
.multiplexing-modal { min-height: 200px; }
.dashboard-tree { max-height: 400px; overflow-y: auto; }
.db-group { margin-bottom: 4px; }
.db-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: var(--radius-sm);
  cursor: pointer; transition: background 0.15s;
}
.db-header:hover { background: var(--color-bg-page); }
.db-toggle { font-size: 10px; color: var(--color-text-tertiary); width: 12px; }
.db-icon { display: flex; color: var(--color-text-tertiary); }
.db-name { flex: 1; font-size: 14px; font-weight: 500; }
.db-status-tag { font-size: 11px; color: var(--color-text-tertiary); padding: 1px 6px; background: var(--color-bg-page); border-radius: 4px; }
.panel-list { padding-left: 36px; }
.panel-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: var(--radius-sm);
  cursor: pointer; transition: all 0.15s;
  border: 1px solid transparent; margin-bottom: 2px;
}
.panel-item:hover { background: var(--color-bg-page); }
.panel-item.selected { border-color: var(--color-primary); background: var(--color-primary-light); }
.panel-icon { display: flex; color: var(--color-text-tertiary); }
.panel-name { flex: 1; font-size: 13px; }
.panel-type { font-size: 11px; color: var(--color-text-tertiary); background: var(--color-bg-page); padding: 0 6px; border-radius: 4px; }
.panel-empty { padding: 8px 10px; font-size: 12px; color: var(--color-text-tertiary); }
</style>
