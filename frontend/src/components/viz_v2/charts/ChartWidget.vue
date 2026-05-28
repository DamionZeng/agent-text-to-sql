<template>
  <div class="chart-widget">
    <ChartRenderer
      :chart-name="panel.title || '图表'"
      :chart-type="chartType"
      :echarts-option="echartsOption"
      :show-header="false"
      :is-dark-mode="isDarkMode"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ChartRenderer from '../../ChartRenderer.vue'

const props = defineProps({
  panel: { type: Object, required: true },
  chartData: { type: Object, default: null },
  isDarkMode: { type: Boolean, default: false },
})

const chartType = computed(() => {
  return props.chartData?.chart_type || props.panel._chartType || props.panel.chart_type || 'bar'
})

const echartsOption = computed(() => {
  return props.chartData?.echarts_option || {}
})
</script>

<style scoped>
.chart-widget {
  width: 100%;
  height: 100%;
}
</style>
