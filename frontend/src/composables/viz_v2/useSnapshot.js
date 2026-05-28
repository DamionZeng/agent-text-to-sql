import { ref, computed } from 'vue'

const MAX_SNAPSHOTS = 50

export function useSnapshot() {
  const snapshots = ref([])
  const currentIndex = ref(-1)

  const canUndo = computed(() => currentIndex.value > 0)
  const canRedo = computed(() => currentIndex.value < snapshots.value.length - 1)

  function takeSnapshot(panels, filters) {
    const snapshot = {
      panels: JSON.parse(JSON.stringify(panels)),
      filters: JSON.parse(JSON.stringify(filters)),
    }
    snapshots.value = snapshots.value.slice(0, currentIndex.value + 1)
    snapshots.value.push(snapshot)
    while (snapshots.value.length > MAX_SNAPSHOTS) {
      snapshots.value.shift()
      currentIndex.value--
    }
    currentIndex.value = snapshots.value.length - 1
  }

  function undo(panels, filters) {
    if (!canUndo.value) return false
    currentIndex.value--
    const s = snapshots.value[currentIndex.value]
    if (!s) return false
    panels.splice(0, panels.length, ...s.panels)
    filters.splice(0, filters.length, ...s.filters)
    return true
  }

  function redo(panels, filters) {
    if (!canRedo.value) return false
    currentIndex.value++
    const s = snapshots.value[currentIndex.value]
    if (!s) return false
    panels.splice(0, panels.length, ...s.panels)
    filters.splice(0, filters.length, ...s.filters)
    return true
  }

  function initSnapshot(panels, filters) {
    snapshots.value = []
    currentIndex.value = -1
    takeSnapshot(panels, filters)
  }

  return { canUndo, canRedo, takeSnapshot, undo, redo, initSnapshot }
}
