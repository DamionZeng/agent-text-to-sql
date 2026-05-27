<template>
  <div class="component-wrapper">
    <!-- Chart Component -->
    <v-chart
      v-if="['bar-chart', 'line-chart'].includes(config.type)"
      class="chart"
      :option="chartOption"
      autoresize
    />
    <!-- Text Component -->
    <div v-else-if="config.type === 'text'" class="text-content">
      {{ config.propValue || '双击编辑文本' }}
    </div>
    <!-- Unknown -->
    <div v-else class="unknown">
      未知组件: {{ config.type }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const props = defineProps({
  config: {
    type: Object,
    required: true
  }
})

const chartOption = computed(() => {
  if (props.config.type === 'bar-chart') {
    return {
      tooltip: {},
      xAxis: { type: 'category', data: ['A', 'B', 'C', 'D'] },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: [10, 20, 30, 40] }]
    }
  }
  if (props.config.type === 'line-chart') {
    return {
      tooltip: {},
      xAxis: { type: 'category', data: ['A', 'B', 'C', 'D'] },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: [40, 30, 20, 10] }]
    }
  }
  return {}
})
</script>

<style scoped>
.component-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.chart {
  width: 100%;
  height: 100%;
}
.text-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
}
.unknown {
  color: red;
}
</style>
