<template>
  <div class="chart-renderer" :class="{ 'dark-mode': isDarkMode }">
    <div class="chart-header" v-if="showHeader && chartType !== 'number_card'">
      <span class="chart-title">{{ chartName }}</span>
      <span class="chart-type-tag">{{ chartTypeLabel }}</span>
    </div>
    <div ref="chartEl" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chartName: { type: String, default: '图表' },
  chartType: { type: String, default: 'bar' },
  echartsOption: { type: Object, default: () => ({}) },
  height: { type: Number, default: null },
  showHeader: { type: Boolean, default: true },
  isDarkMode: { type: Boolean, default: false },
})

const chartEl = ref(null)
let chartInstance = null
let resizeObserver = null

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

const getDarkThemeOverrides = () => {
  const textColor = 'rgba(255, 255, 255, 0.85)'
  const subTextColor = 'rgba(255, 255, 255, 0.55)'
  const axisLineColor = 'rgba(255, 255, 255, 0.15)'
  const splitLineColor = 'rgba(255, 255, 255, 0.08)'

  return {
    textStyle: { color: textColor },
    title: { textStyle: { color: textColor }, subtextStyle: { color: subTextColor } },
    legend: { textStyle: { color: textColor }, pageTextStyle: { color: textColor } },
    tooltip: {
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      textStyle: { color: textColor },
    },
    xAxis: {
      axisLine: { lineStyle: { color: axisLineColor } },
      axisTick: { lineStyle: { color: axisLineColor } },
      axisLabel: { color: subTextColor },
      splitLine: { lineStyle: { color: splitLineColor } },
    },
    yAxis: {
      axisLine: { lineStyle: { color: axisLineColor } },
      axisTick: { lineStyle: { color: axisLineColor } },
      axisLabel: { color: subTextColor },
      splitLine: { lineStyle: { color: splitLineColor } },
    },
    radar: {
      axisName: { color: subTextColor },
      splitLine: { lineStyle: { color: splitLineColor } },
      axisLine: { lineStyle: { color: axisLineColor } },
    },
  }
}

const mergeDarkTheme = (option) => {
  const darkOverrides = getDarkThemeOverrides()
  const merged = { ...option, backgroundColor: 'transparent' }

  if (merged.textStyle) {
    merged.textStyle = { ...darkOverrides.textStyle, ...merged.textStyle }
  } else {
    merged.textStyle = darkOverrides.textStyle
  }

  if (merged.title) {
    merged.title = { ...darkOverrides.title, ...merged.title }
    if (option.title?.textStyle) {
      merged.title.textStyle = { ...darkOverrides.title.textStyle, ...option.title.textStyle }
    }
  }

  if (merged.legend) {
    merged.legend = { ...darkOverrides.legend, ...merged.legend }
    if (option.legend?.textStyle) {
      merged.legend.textStyle = { ...darkOverrides.legend.textStyle, ...option.legend.textStyle }
    }
  }

  if (merged.tooltip) {
    merged.tooltip = { ...darkOverrides.tooltip, ...merged.tooltip }
  }

  if (merged.xAxis) {
    if (Array.isArray(merged.xAxis)) {
      merged.xAxis = merged.xAxis.map((ax) => ({ ...darkOverrides.xAxis, ...ax }))
    } else {
      merged.xAxis = { ...darkOverrides.xAxis, ...merged.xAxis }
    }
  }

  if (merged.yAxis) {
    if (Array.isArray(merged.yAxis)) {
      merged.yAxis = merged.yAxis.map((ax) => ({ ...darkOverrides.yAxis, ...ax }))
    } else {
      merged.yAxis = { ...darkOverrides.yAxis, ...merged.yAxis }
    }
  }

  if (merged.radar) {
    merged.radar = { ...darkOverrides.radar, ...merged.radar }
  }

  return merged
}

const initChart = () => {
  if (!chartEl.value) return
  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartEl.value)

  let option = {
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

  if (props.isDarkMode) {
    option = mergeDarkTheme(option)
  }

  chartInstance.setOption(option, true)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

watch(() => props.echartsOption, () => {
  nextTick(() => initChart())
}, { deep: true })

watch(() => props.chartType, () => {
  nextTick(() => initChart())
})

watch(() => props.isDarkMode, () => {
  nextTick(() => initChart())
})

onMounted(() => {
  nextTick(() => {
    initChart()
    if (chartEl.value && window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        handleResize()
      })
      resizeObserver.observe(chartEl.value)
    }
  })
})

onBeforeUnmount(() => {
  if (resizeObserver && chartEl.value) {
    resizeObserver.unobserve(chartEl.value)
    resizeObserver = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.chart-renderer {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-bg-surface);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-bg-page);
  flex-shrink: 0;
}

.chart-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.chart-type-tag {
  font-size: 11px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-page);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 0;
}
</style>
