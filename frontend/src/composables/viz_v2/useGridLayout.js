import { ref, watch } from 'vue'

export function useGridLayout(store) {
  const isDraggable = ref(true)
  const isResizable = ref(true)
  const colNum = ref(12)
  const rowHeight = ref(100)
  const margin = ref([12, 12])

  function onLayoutUpdated(newLayout) {
    store.updateLayout(newLayout)
  }

  function onItemSelected(itemId) {
    store.selectPanel(itemId)
  }

  return {
    isDraggable,
    isResizable,
    colNum,
    rowHeight,
    margin,
    onLayoutUpdated,
    onItemSelected,
  }
}