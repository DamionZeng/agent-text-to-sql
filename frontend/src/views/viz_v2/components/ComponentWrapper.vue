<template>
  <div class="component-wrapper">
    <!-- Chart Component -->
    <v-chart
      v-if="['bar-chart', 'line-chart'].includes(config.type)"
      class="chart"
      :option="chartOption"
      autoresize
    />
    <!-- Number Card Component -->
    <div v-else-if="config.type === 'number-card'" class="number-card">
      <div class="number-value">{{ config.propValue || 0 }}</div>
      <div class="number-label">{{ config.name || '数字卡片' }}</div>
    </div>
    <!-- Text Component -->
    <div v-else-if="config.type === 'text'" class="text-content">
      {{ config.propValue || '文本内容' }}
    </div>
    <!-- Unknown -->
    <div v-else class="unknown">
      未知类型: {{ config.type }}
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
.number-card {
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
.number-value {
  font-size: 2.4em;
  font-weight: 700;
  color: #36cfc9;
  font-family: 'DIN', 'Helvetica Neue', sans-serif;
  line-height: 1.2;
}
.number-label {
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.65);
  margin-top: 4px;
}
.unknown {
  color: red;
}
</style>
