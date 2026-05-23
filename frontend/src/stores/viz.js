import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = '/api/viz'

export const useVizStore = defineStore('viz', () => {
  const dashboard = ref(null)
  const panels = ref([])
  const filters = ref([])
  const loading = ref(false)

  const selectedPanelId = ref(null)

  const selectedPanel = computed(() =>
    panels.value.find((p) => p.id === selectedPanelId.value) || null
  )

  const gridLayout = computed(() =>
    panels.value.map((p) => ({
      i: p.id,
      x: p.layout_x,
      y: p.layout_y,
      w: p.layout_w,
      h: p.layout_h,
    }))
  )

  async function loadDashboard(dashboardId) {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/dashboards/${dashboardId}`)
      if (!res.ok) throw new Error('加载大屏失败')
      const data = await res.json()
      dashboard.value = data.dashboard
      panels.value = data.panels || []
      filters.value = data.filters || []
      return data
    } finally {
      loading.value = false
    }
  }

  function selectPanel(panelId) {
    selectedPanelId.value = panelId
  }

  function clearSelection() {
    selectedPanelId.value = null
  }

  async function updateLayout(newLayout) {
    const layoutMap = new Map(newLayout.map((l) => [l.i, l]))
    const updated = panels.value
      .filter((p) => layoutMap.has(p.id))
      .map((p) => {
        const l = layoutMap.get(p.id)
        return {
          id: p.id,
          layout_x: l.x,
          layout_y: l.y,
          layout_w: l.w,
          layout_h: l.h,
        }
      })
    if (updated.length === 0) return

    panels.value = panels.value.map((p) => {
      const l = layoutMap.get(p.id)
      if (l) {
        return { ...p, layout_x: l.x, layout_y: l.y, layout_w: l.w, layout_h: l.h }
      }
      return p
    })

    await fetch(`${API_BASE}/dashboards/${dashboard.value.id}/panels/reorder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ panels: updated }),
    })
  }

  async function addPanel(dashboardId, chartConfigId, title = null, layout = {}) {
    const body = {
      chart_config_id: chartConfigId,
      title,
      layout_x: layout.x || 0,
      layout_y: layout.y || 0,
      layout_w: layout.w || 6,
      layout_h: layout.h || 4,
    }
    const res = await fetch(`${API_BASE}/dashboards/${dashboardId}/panels`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error('添加面板失败')
    const panel = await res.json()
    panels.value.push(panel)
    return panel
  }

  async function removePanel(dashboardId, panelId) {
    const res = await fetch(`${API_BASE}/dashboards/${dashboardId}/panels/${panelId}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error('删除面板失败')
    panels.value = panels.value.filter((p) => p.id !== panelId)
    if (selectedPanelId.value === panelId) {
      selectedPanelId.value = null
    }
  }

  async function updatePanelConfig(panelId, updates) {
    const res = await fetch(`${API_BASE}/dashboards/${dashboard.value.id}/panels/${panelId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    if (!res.ok) throw new Error('更新面板失败')
    const updated = await res.json()
    panels.value = panels.value.map((p) => (p.id === panelId ? updated : p))
  }

  async function saveDashboard(updates) {
    const res = await fetch(`${API_BASE}/dashboards/${dashboard.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    if (!res.ok) throw new Error('保存大屏失败')
    const updated = await res.json()
    dashboard.value = updated
    return updated
  }

  async function loadDashboardList(offset = 0, limit = 20, status = null) {
    const params = new URLSearchParams({ offset, limit })
    if (status) params.append('status', status)
    const res = await fetch(`${API_BASE}/dashboards?${params}`)
    if (!res.ok) throw new Error('加载大屏列表失败')
    return await res.json()
  }

  async function createDashboard(data) {
    const res = await fetch(`${API_BASE}/dashboards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('创建大屏失败')
    return await res.json()
  }

  async function deleteDashboard(dashboardId) {
    const res = await fetch(`${API_BASE}/dashboards/${dashboardId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('删除大屏失败')
  }

  return {
    dashboard,
    panels,
    filters,
    loading,
    selectedPanelId,
    selectedPanel,
    gridLayout,
    loadDashboard,
    selectPanel,
    clearSelection,
    updateLayout,
    addPanel,
    removePanel,
    updatePanelConfig,
    saveDashboard,
    loadDashboardList,
    createDashboard,
    deleteDashboard,
  }
})