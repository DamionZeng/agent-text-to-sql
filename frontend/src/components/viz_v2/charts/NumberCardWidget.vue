<template>
  <div class="number-card-widget">
    <div class="nc-value">{{ displayValue }}</div>
    <div class="nc-label">{{ panel.title || '数字卡片' }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  panel: { type: Object, required: true },
  chartData: { type: Object, default: null },
  isDarkMode: { type: Boolean, default: false },
})

const displayValue = computed(() => {
  if (props.chartData?.echarts_option?.series?.[0]?.data != null) {
    return props.chartData.echarts_option.series[0].data
  }
  return '--'
})
</script>

<style scoped>
.number-card-widget {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a2a4a 0%, #0d1b2a 100%);
  border-radius: 8px;
  padding: 12px;
}
.nc-value {
  font-size: 2.4em;
  font-weight: 700;
  color: #36cfc9;
  font-family: 'DIN', 'Helvetica Neue', sans-serif;
  line-height: 1.2;
}
.nc-label {
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.65);
  margin-top: 4px;
}
</style>
