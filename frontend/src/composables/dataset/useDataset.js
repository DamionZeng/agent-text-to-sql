import { ref } from 'vue'

const API_BASE = '/api/datasets'
const META_API_BASE = '/api/metadata'

export function useDataset() {
  const datasets = ref([])
  const loading = ref(false)

  async function fetchList(groupId = null) {
    loading.value = true
    try {
      const url = groupId ? `${API_BASE}?group_id=${groupId}` : API_BASE
      const res = await fetch(url)
      if (!res.ok) throw new Error('加载数据集列表失败')
      const data = await res.json()
      datasets.value = data || []
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchDataset(id) {
    const res = await fetch(`${API_BASE}/${id}`)
    if (!res.ok) throw new Error('加载数据集详情失败')
    return await res.json()
  }

  async function createDataset(data) {
    const res = await fetch(`${API_BASE}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('创建数据集失败')
    return await res.json()
  }

  async function updateDataset(id, data) {
    const res = await fetch(`${API_BASE}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('更新数据集失败')
    return await res.json()
  }

  async function deleteDataset(id) {
    const res = await fetch(`${API_BASE}/${id}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error('删除数据集失败')
    return await res.json()
  }

  // ========== Groups ==========

  async function fetchGroups() {
    const res = await fetch(`${API_BASE}/groups`)
    if (!res.ok) throw new Error('加载分组失败')
    return await res.json()
  }

  async function createGroup(name) {
    const res = await fetch(`${API_BASE}/groups`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!res.ok) throw new Error('创建分组失败')
    return await res.json()
  }

  async function deleteGroup(id) {
    const res = await fetch(`${API_BASE}/groups/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('删除分组失败')
    return await res.json()
  }

  // Fetch all datasources for the dropdown
  async function fetchDatasources() {
    const res = await fetch(`${META_API_BASE}/datasources`)
    if (!res.ok) throw new Error('加载数据源失败')
    return await res.json()
  }

  // Fetch schema (tables and columns) for a specific datasource
  async function fetchDatasourceSchema(datasourceId) {
    const res = await fetch(`${META_API_BASE}/datasources/${datasourceId}/schema`)
    if (!res.ok) throw new Error('加载数据源Schema失败')
    return await res.json()
  }

  async function executeSql(datasourceId, sql) {
    const res = await fetch(`${META_API_BASE}/datasources/${datasourceId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'SQL执行失败')
    }
    return await res.json()
  }

  async function fetchTableMetadata(datasourceId, tableName) {
    const res = await fetch(`${META_API_BASE}/datasources/${datasourceId}/tables/${tableName}/metadata`)
    if (!res.ok) throw new Error('加载元数据失败')
    return await res.json()
  }

  return {
    datasets,
    loading,
    fetchList,
    fetchDataset,
    createDataset,
    updateDataset,
    deleteDataset,
    fetchGroups,
    createGroup,
    deleteGroup,
    fetchDatasources,
    fetchDatasourceSchema,
    executeSql,
    fetchTableMetadata
  }
}
