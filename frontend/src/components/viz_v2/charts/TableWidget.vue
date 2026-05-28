<template>
  <div class="table-widget">
    <div class="tw-placeholder">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="3" y1="9" x2="21" y2="9"/>
        <line x1="3" y1="15" x2="21" y2="15"/>
        <line x1="9" y1="3" x2="9" y2="21"/>
      </svg>
      <span>{{ panel.title || '数据表格' }}</span>
      <span class="tw-hint">双击配置数据源</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  panel: { type: Object, required: true },
  chartData: { type: Object, default: null },
  isDarkMode: { type: Boolean, default: false },
})
</script>

<style scoped>
.table-widget {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
}
.tw-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--color-text-tertiary);
}
.tw-hint {
  font-size: 11px;
  color: var(--color-text-tertiary);
  opacity: 0.6;
}
</style>
