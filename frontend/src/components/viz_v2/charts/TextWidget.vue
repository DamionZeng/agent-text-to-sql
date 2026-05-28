<template>
  <div class="text-widget">
    <div class="tw-content" v-html="displayContent"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  panel: { type: Object, required: true },
  chartData: { type: Object, default: null },
  isDarkMode: { type: Boolean, default: false },
})

const displayContent = computed(() => {
  return props.chartData?.echarts_option?.text || props.panel.title || '文本内容'
})
</script>

<style scoped>
.text-widget {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  overflow: auto;
}
.tw-content {
  font-size: 16px;
  color: var(--color-text-primary);
  text-align: center;
  word-break: break-word;
}
</style>
