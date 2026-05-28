<template>
  <a-modal
    v-model:open="visible"
    title="仪表板配置"
    width="520px"
    @ok="handleConfirm"
  >
    <a-form layout="vertical" size="small">
      <a-divider>画布设置</a-divider>
      <a-form-item label="自适应模式">
        <a-radio-group v-model:value="config.canvasAdaption">
          <a-radio value="width">宽度自适应</a-radio>
          <a-radio value="scale">等比缩放</a-radio>
        </a-radio-group>
      </a-form-item>
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="画布宽度 (px)">
            <a-input-number v-model:value="config.canvasWidth" :min="800" :max="7680" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="画布高度 (px)">
            <a-input-number v-model:value="config.canvasHeight" :min="400" :max="4320" style="width:100%" />
          </a-form-item>
        </a-col>
      </a-row>

      <a-divider>背景设置</a-divider>
      <a-form-item label="背景颜色">
        <a-input v-model:value="config.backgroundColor" placeholder="#FFFFFF 或 rgba">
          <template #prefix>
            <span class="color-preview" :style="{ background: config.backgroundColor }"></span>
          </template>
        </a-input>
      </a-form-item>
      <a-form-item label="背景透明度">
        <a-slider v-model:value="config.backgroundOpacity" :min="0" :max="1" :step="0.1" />
      </a-form-item>
      <a-form-item label="背景图片 URL">
        <a-input v-model:value="config.backgroundImage" placeholder="输入图片链接，留空为无" />
      </a-form-item>

      <a-divider>网格设置</a-divider>
      <a-form-item label="显示网格线">
        <a-switch v-model:checked="config.showGridLines" />
      </a-form-item>
      <a-row :gutter="12" v-if="config.showGridLines">
        <a-col :span="12">
          <a-form-item label="网格列数">
            <a-input-number v-model:value="config.gridColumns" :min="4" :max="24" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="网格行高 (px)">
            <a-input-number v-model:value="config.gridRowHeight" :min="30" :max="200" style="width:100%" />
          </a-form-item>
        </a-col>
      </a-row>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  dashboard: { type: Object, default: null },
})

const emit = defineEmits(['update:open', 'apply'])

const visible = ref(false)
const config = ref(getDefaultConfig())

function getDefaultConfig() {
  return {
    canvasAdaption: 'width',
    canvasWidth: 1920,
    canvasHeight: 1080,
    backgroundColor: '#FFFFFF',
    backgroundOpacity: 1,
    backgroundImage: '',
    showGridLines: false,
    gridColumns: 12,
    gridRowHeight: 100,
  }
}

watch(() => props.open, (val) => {
  visible.value = val
  if (val && props.dashboard) {
    const d = props.dashboard
    config.value = {
      canvasAdaption: d.canvas_adaption || 'width',
      canvasWidth: d.canvas_width || 1920,
      canvasHeight: d.canvas_height || 1080,
      backgroundColor: d.background_color || '#FFFFFF',
      backgroundOpacity: d.background_opacity ?? 1,
      backgroundImage: d.background_image || '',
      showGridLines: d.show_grid_lines ?? false,
      gridColumns: d.grid_columns || 12,
      gridRowHeight: d.grid_row_height || 100,
    }
  }
})

watch(visible, (val) => { emit('update:open', val) })

function handleConfirm() {
  emit('apply', { ...config.value })
  visible.value = false
}
</script>

<style scoped>
.color-preview {
  display: inline-block;
  width: 18px;
  height: 18px;
  border-radius: 3px;
  border: 1px solid var(--color-border);
  vertical-align: middle;
}
</style>
