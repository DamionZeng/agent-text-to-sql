<template>
  <div class="chart-renderer">
    <div class="chart-header">
      <span class="chart-title">{{ chartName }}</span>
      <span class="chart-type-tag">{{ chartTypeLabel }}</span>
    </div>
    <div ref="chartEl" class="chart-container" :style="{ height: height + 'px' }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chartName: { type: String, default: '图表' },
  chartType: { type: String, default: 'bar' },
  echartsOption: { type: Object, default: () => ({}) },
  height: { type: Number, default: 400 },
})

const chartEl = ref(null)
let chartInstance = null

const chartTypeLabelMap = {
  line: '折线图',
  bar: '柱状图',
  pie: '饼图',
  scatter: '散点图',
  radar: '雷达图',
  gauge: '仪表盘',
  number_card: '数字卡片',
  table: '数据表格',
  text: '文本',
  heatmap: '热力图',
  funnel: '漏斗图',
  map: '地图',
}

const chartTypeLabel = computed(() => chartTypeLabelMap[props.chartType] || props.chartType)

const initChart = () => {
  if (!chartEl.value) return
  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartEl.value)

  const option = {
    ...props.echartsOption,
    backgroundColor: 'transparent',
  }

  if (option.grid && !Array.isArray(option.grid)) {
    option.grid = {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
      ...option.grid,
    }
  }

  chartInstance.setOption(option, true)
}

watch(() => props.echartsOption, () => {
  nextTick(() => initChart())
}, { deep: true })

onMounted(() => {
  nextTick(() => initChart())
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<script>
import { computed } from 'vue'
</script>

<style scoped>
.chart-renderer {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  margin: 8px 0;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.chart-title {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.chart-type-tag {
  font-size: 11px;
  color: #888;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
}

.chart-container {
  width: 100%;
  min-height: 200px;
}
</style>