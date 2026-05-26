import { ref } from 'vue'

const API_BASE = '/api/viz'

export function useDashboard() {
  const dashboards = ref([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchList(offset = 0, limit = 20, status = null) {
    loading.value = true
    try {
      const params = new URLSearchParams({ offset, limit })
      if (status) params.append('status', status)
      const res = await fetch(`${API_BASE}/dashboards?${params}`)
      if (!res.ok) throw new Error('加载大屏列表失败')
      const data = await res.json()
      dashboards.value = data.items || []
      total.value = data.total || 0
      return data
    } finally {
      loading.value = false
    }
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

  async function deleteDashboard(id) {
    const res = await fetch(`${API_BASE}/dashboards/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('删除大屏失败')
  }

  async function updateDashboard(id, data) {
    const res = await fetch(`${API_BASE}/dashboards/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('更新大屏失败')
    return await res.json()
  }

  return {
    dashboards,
    total,
    loading,
    fetchList,
    createDashboard,
    deleteDashboard,
    updateDashboard,
  }
}