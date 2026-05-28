<template>
  <a-modal
    v-model:open="visible"
    title="仪表板配置"
    width="560px"
    @ok="handleConfirm"
    :bodyStyle="{ maxHeight: '60vh', overflowY: 'auto' }"
  >
    <a-form layout="vertical" size="small">
      <a-collapse v-model:activeKey="activeKeys" :bordered="false">
        <a-collapse-panel key="canvas" header="画布设置">
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
        </a-collapse-panel>

        <a-collapse-panel key="background" header="背景设置">
          <a-form-item label="背景颜色">
            <div class="color-input-wrapper">
              <input
                ref="colorInputRef"
                type="color"
                :value="config.backgroundColor"
                @input="onColorInput"
                class="native-color-picker"
              />
              <a-input
                :value="config.backgroundColor"
                @change="onColorTextChange"
                size="small"
                class="color-text-input"
              >
                <template #prefix>
                  <span
                    class="color-swatch-inline"
                    :style="{ background: config.backgroundColor }"
                    @click="openColorPicker"
                  ></span>
                </template>
              </a-input>
            </div>
          </a-form-item>
          <a-form-item label="背景透明度">
            <div class="opacity-row">
              <a-slider v-model:value="config.backgroundOpacity" :min="0" :max="1" :step="0.05" style="flex:1" />
              <span class="opacity-value">{{ Math.round(config.backgroundOpacity * 100) }}%</span>
            </div>
          </a-form-item>
          <a-form-item label="背景图片">
            <div class="bg-image-upload">
              <div class="bg-preview-area" v-if="config.backgroundImage" @click="triggerUpload">
                <img :src="config.backgroundImage" alt="背景预览" class="bg-preview-img" />
                <div class="bg-preview-overlay">
                  <UploadOutlined /> 更换图片
                </div>
              </div>
              <div class="bg-upload-trigger" v-else @click="triggerUpload">
                <PictureOutlined class="upload-icon" />
                <span>点击上传背景图片</span>
                <span class="upload-hint">支持 JPG/PNG/GIF/WEBP</span>
              </div>
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                style="display:none"
                @change="onFileChange"
              />
              <div class="bg-actions" v-if="config.backgroundImage">
                <a-button size="small" @click="triggerUpload">
                  <UploadOutlined /> 更换
                </a-button>
                <a-button size="small" danger @click="removeBackgroundImage">
                  <DeleteOutlined /> 移除
                </a-button>
              </div>
            </div>
          </a-form-item>
          <a-form-item label="背景图填充方式" v-if="config.backgroundImage">
            <a-radio-group v-model:value="config.backgroundSize" size="small">
              <a-radio-button value="cover">覆盖填充</a-radio-button>
              <a-radio-button value="contain">完整显示</a-radio-button>
              <a-radio-button value="auto">原始大小</a-radio-button>
            </a-radio-group>
          </a-form-item>
        </a-collapse-panel>

        <a-collapse-panel key="grid" header="网格设置">
          <a-form-item label="显示网格线">
            <a-switch v-model:checked="config.showGridLines" />
            <span class="form-item-desc">开启后在画布上显示辅助网格线</span>
          </a-form-item>
          <a-row :gutter="12">
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
        </a-collapse-panel>
      </a-collapse>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { PictureOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  dashboard: { type: Object, default: null },
})

const emit = defineEmits(['update:open', 'apply'])

const visible = ref(false)
const activeKeys = ref(['canvas', 'background', 'grid'])
const fileInputRef = ref(null)
const colorInputRef = ref(null)
const config = ref(getDefaultConfig())

function getDefaultConfig() {
  return {
    canvasAdaption: 'width',
    canvasWidth: 1920,
    canvasHeight: 1080,
    backgroundColor: '#FFFFFF',
    backgroundOpacity: 1,
    backgroundImage: '',
    backgroundSize: 'cover',
    showGridLines: false,
    gridColumns: 12,
    gridRowHeight: 100,
  }
}

watch(() => props.open, (val) => {
  visible.value = val
  if (val && props.dashboard) {
    const lc = props.dashboard.layout_config || {}
    config.value = {
      canvasAdaption: lc.canvas_adaption || 'width',
      canvasWidth: lc.canvas_width || 1920,
      canvasHeight: lc.canvas_height || 1080,
      backgroundColor: lc.background_color || '#FFFFFF',
      backgroundOpacity: lc.background_opacity ?? 1,
      backgroundImage: lc.background_image || '',
      backgroundSize: lc.background_size || 'cover',
      showGridLines: lc.show_grid_lines ?? false,
      gridColumns: lc.grid_columns || 12,
      gridRowHeight: lc.grid_row_height || 100,
    }
  }
})

watch(visible, (val) => { emit('update:open', val) })

function triggerUpload() {
  fileInputRef.value?.click()
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return

  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过 5MB')
    return
  }

  const reader = new FileReader()
  reader.onload = (evt) => {
    config.value.backgroundImage = evt.target.result
  }
  reader.readAsDataURL(file)

  e.target.value = ''
}

function removeBackgroundImage() {
  config.value.backgroundImage = ''
  config.value.backgroundSize = 'cover'
}

function openColorPicker() {
  colorInputRef.value?.click()
}

function onColorInput(e) {
  config.value.backgroundColor = e.target.value
}

function onColorTextChange(e) {
  let val = e.target.value.trim()
  if (!val.startsWith('#')) val = '#' + val
  if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
    config.value.backgroundColor = val
  }
}

function handleConfirm() {
  emit('apply', { ...config.value })
  visible.value = false
}
</script>

<style scoped>
.color-input-wrapper {
  position: relative;
  width: 100%;
}
.native-color-picker {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 1;
}
.color-text-input {
  width: 100%;
}
.color-swatch-inline {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.15);
  cursor: pointer;
  vertical-align: middle;
}
.opacity-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.opacity-value {
  font-size: 13px;
  color: var(--color-text-secondary);
  min-width: 36px;
  text-align: right;
}
.form-item-desc {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-left: 8px;
}
.bg-image-upload {
  width: 100%;
}
.bg-preview-area {
  position: relative;
  width: 100%;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  cursor: pointer;
  margin-bottom: 8px;
}
.bg-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.bg-preview-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.2s;
}
.bg-preview-area:hover .bg-preview-overlay {
  opacity: 1;
}
.bg-upload-trigger {
  width: 100%;
  height: 100px;
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-text-tertiary);
}
.bg-upload-trigger:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-light);
}
.upload-icon {
  font-size: 28px;
}
.upload-hint {
  font-size: 11px;
}
.bg-actions {
  display: flex;
  gap: 8px;
}
:deep(.ant-collapse) {
  background: transparent;
}
:deep(.ant-collapse-item) {
  border-bottom: 1px solid var(--color-border-light);
}
:deep(.ant-collapse-header) {
  font-weight: 600;
  font-size: 14px;
  padding: 12px 0 !important;
}
:deep(.ant-collapse-content-box) {
  padding: 4px 0 16px !important;
}
</style>
