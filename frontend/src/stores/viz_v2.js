import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = '/api/viz'

export const useVizStore = defineStore('viz', () => {
  const dashboard = ref(null)
  const panels = ref([])
  const filters = ref([])
  const loading = ref(false)
  const pendingChanges = ref(false)
  const _deletedPanelIds = ref([])

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

  // ─── Load ─────────────────────────────────────────
  async function loadDashboard(dashboardId) {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/dashboards/${dashboardId}`)
      if (!res.ok) throw new Error('加载大屏失败')
      const data = await res.json()
      dashboard.value = data.dashboard
      panels.value = data.panels || []
      filters.value = data.filters || []
      _deletedPanelIds.value = []
      pendingChanges.value = false
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

  // ─── Local State Mutations (no backend calls) ─────
  function addPanelLocal(chartConfigId, title = null, layout = {}, chartType = null) {
    const panel = {
      id: 'local_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      dashboard_id: dashboard.value?.id || '',
      chart_config_id: chartConfigId,
      chart_type: chartType,
      title: title || '未命名面板',
      layout_x: layout.x || 0,
      layout_y: layout.y || 0,
      layout_w: layout.w || 6,
      layout_h: layout.h || 4,
      sort_order: panels.value.length,
      hidden: false,
      _isLocal: true,
    }
    if (chartType) {
      panel._chartType = chartType
    }
    panels.value.push(panel)
    pendingChanges.value = true
    return panel
  }

  function removePanelLocal(panelId) {
    const panel = panels.value.find(p => p.id === panelId)
    if (panel && !panel._isLocal) {
      _deletedPanelIds.value.push(panelId)
    }
    panels.value = panels.value.filter((p) => p.id !== panelId)
    if (selectedPanelId.value === panelId) {
      selectedPanelId.value = null
    }
    pendingChanges.value = true
  }

  function updatePanelConfigLocal(panelId, updates) {
    panels.value = panels.value.map((p) => {
      if (p.id === panelId) {
        const updated = { ...p, ...updates }
        if (updates.chart_type) {
          updated._chartType = updates.chart_type
        }
        return updated
      }
      return p
    })
    pendingChanges.value = true
  }

  function updateLayoutLocal(newLayout) {
    const layoutMap = new Map(newLayout.map((l) => [l.i, l]))
    panels.value = panels.value.map((p) => {
      const l = layoutMap.get(p.id)
      if (l) {
        return { ...p, layout_x: l.x, layout_y: l.y, layout_w: l.w, layout_h: l.h }
      }
      return p
    })
    pendingChanges.value = true
  }

  function updateDashboardLocal(updates) {
    if (dashboard.value) {
      dashboard.value = { ...dashboard.value, ...updates }
      pendingChanges.value = true
    }
  }

  // ─── Remote API Calls ─────────────────────────────
  async function addPanel(dashboardId, chartConfigId, title = null, layout = {}, chartType = null) {
    const body = {
      chart_config_id: chartConfigId,
      chart_type: chartType,
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
    if (chartType) {
      panel._chartType = chartType
      panel.chart_type = chartType
    }
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
    const oldPanel = panels.value.find(p => p.id === panelId)
    const res = await fetch(`${API_BASE}/dashboards/${dashboard.value.id}/panels/${panelId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    if (!res.ok) throw new Error('更新面板失败')
    const updated = await res.json()
    if (oldPanel) {
      updated._chartType = oldPanel._chartType || updated.chart_type
    }
    panels.value = panels.value.map((p) => (p.id === panelId ? updated : p))
  }

  async function updateChartConfig(chartId, updates) {
    const res = await fetch(`${API_BASE}/charts/${chartId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    if (!res.ok) throw new Error('更新图表配置失败')
    return await res.json()
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

  // ─── Full Save (dashboard + panels + layout) ──────
  async function saveAll() {
    if (!dashboard.value) return

    // 1. Save dashboard basic info
    const res = await fetch(`${API_BASE}/dashboards/${dashboard.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dashboard.value),
    })
    if (!res.ok) throw new Error('保存大屏基本信息失败')

    // 2. Sync all panels
    for (const panel of panels.value) {
      if (panel._isLocal) {
        // Create new panel on backend
        const createRes = await fetch(`${API_BASE}/dashboards/${dashboard.value.id}/panels`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chart_config_id: panel.chart_config_id,
            chart_type: panel.chart_type,
            title: panel.title,
            layout_x: panel.layout_x,
            layout_y: panel.layout_y,
            layout_w: panel.layout_w,
            layout_h: panel.layout_h,
            sort_order: panel.sort_order,
            hidden: panel.hidden ?? false,
          }),
        })
        if (createRes.ok) {
          const created = await createRes.json()
          panel.id = created.id
          panel._isLocal = false
        }
      } else {
        // Update existing panel
        await fetch(`${API_BASE}/dashboards/${dashboard.value.id}/panels/${panel.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chart_config_id: panel.chart_config_id,
            chart_type: panel.chart_type,
            title: panel.title,
            layout_x: panel.layout_x,
            layout_y: panel.layout_y,
            layout_w: panel.layout_w,
            layout_h: panel.layout_h,
            sort_order: panel.sort_order,
            hidden: panel.hidden ?? false,
          }),
        })
      }
    }

    // 3. Delete panels that were removed locally
    for (const deletedId of _deletedPanelIds.value) {
      await fetch(`${API_BASE}/dashboards/${dashboard.value.id}/panels/${deletedId}`, {
        method: 'DELETE',
      })
    }
    _deletedPanelIds.value = []

    pendingChanges.value = false
    return true
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
    pendingChanges,
    selectedPanelId,
    selectedPanel,
    gridLayout,
    loadDashboard,
    selectPanel,
    clearSelection,
    // Local mutations
    addPanelLocal,
    removePanelLocal,
    updatePanelConfigLocal,
    updateLayoutLocal,
    updateDashboardLocal,
    // Remote APIs
    updateLayout,
    addPanel,
    removePanel,
    updatePanelConfig,
    updateChartConfig,
    saveDashboard,
    saveAll,
    loadDashboardList,
    createDashboard,
    deleteDashboard,
  }
})
