<template>
  <div class="global-filter-bar" v-if="filters.length > 0">
    <div class="filter-item" v-for="f in filters" :key="f.id">
      <span class="filter-label">{{ f.label }}</span>
      <a-date-picker
        v-if="f.filter_type === 'date_range'"
        v-model:value="filterValues[f.id]"
        size="small"
        style="width: 220px"
        @change="onFilterChange(f)"
      />
      <a-select
        v-else-if="f.filter_type === 'select'"
        v-model:value="filterValues[f.id]"
        size="small"
        style="width: 160px"
        :options="getFilterOptions(f)"
        @change="onFilterChange(f)"
      />
      <a-select
        v-else-if="f.filter_type === 'multi_select'"
        v-model:value="filterValues[f.id]"
        mode="multiple"
        size="small"
        style="width: 200px"
        :options="getFilterOptions(f)"
        @change="onFilterChange(f)"
      />
      <a-input
        v-else
        v-model:value="filterValues[f.id]"
        size="small"
        style="width: 160px"
        :placeholder="`输入${f.label}`"
        @change="onFilterChange(f)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const props = defineProps({
  filters: { type: Array, default: () => [] },
})

const emit = defineEmits(['filter-change'])

const filterValues = reactive({})

function getFilterOptions(filter) {
  if (filter.config?.options) {
    return filter.config.options
  }
  return []
}

function onFilterChange(filter) {
  emit('filter-change', {
    filterId: filter.id,
    name: filter.name,
    value: filterValues[filter.id],
    targetPanels: filter.target_panels,
  })
}
</script>

<style scoped>
.global-filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
  white-space: nowrap;
}
</style>