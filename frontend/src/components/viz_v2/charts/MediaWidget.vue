<template>
  <div class="media-widget">
    <div v-if="mediaType === 'image'" class="mw-image">
      <img v-if="mediaUrl" :src="mediaUrl" class="mw-img" />
      <div v-else class="mw-placeholder">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        <span>{{ panel.title || '图片' }}</span>
      </div>
    </div>
    <div v-else-if="mediaType === 'video'" class="mw-placeholder">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <polygon points="23 7 16 12 23 17 23 7"/>
        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
      </svg>
      <span>{{ panel.title || '视频' }}</span>
    </div>
    <div v-else-if="mediaType === 'iframe'" class="mw-placeholder">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span>{{ panel.title || '网页' }}</span>
    </div>
    <div v-else class="mw-placeholder">
      <span>{{ panel.title || '媒体' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  panel: { type: Object, required: true },
  chartData: { type: Object, default: null },
  isDarkMode: { type: Boolean, default: false },
})

const mediaType = computed(() => {
  return props.panel._chartType || props.panel.chart_type || 'image'
})

const mediaUrl = computed(() => {
  return props.chartData?.echarts_option?.url || ''
})
</script>

<style scoped>
.media-widget {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.mw-image {
  width: 100%;
  height: 100%;
}
.mw-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.mw-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--color-text-tertiary);
}
</style>
