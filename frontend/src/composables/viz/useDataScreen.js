import { ref } from 'vue'

const API_BASE = '/api/viz/data-screens'

export function useDataScreen() {
  const screens = ref([])
  const loading = ref(false)

  async function fetchList() {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}`)
      if (!res.ok) throw new Error('加载仪表板列表失败')
      const data = await res.json()
      screens.value = data || []
      return data
    } finally {
      loading.value = false
    }
  }

  async function createScreen(data) {
    const res = await fetch(`${API_BASE}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('创建大屏失败')
    return await res.json()
  }

  return {
    screens,
    loading,
    fetchList,
    createScreen
  }
}
