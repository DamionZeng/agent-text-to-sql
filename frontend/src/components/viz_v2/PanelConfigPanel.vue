<template>
  <div class="panel-config-panel">
    <a-tabs v-model:activeKey="activeTab" size="small">
      <a-tab-pane key="basic" tab="基础">
        <div class="config-form">
          <a-form layout="vertical" size="small">
            <a-form-item label="面板标题">
              <a-input v-model:value="form.title" placeholder="输入面板标题" />
            </a-form-item>
            <a-form-item label="图表类型">
              <a-select v-model:value="form.chartType" placeholder="选择图表类型">
                <a-select-option v-for="(label, type) in chartTypeNames" :key="type" :value="type">{{ label }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
      </a-tab-pane>
      <a-tab-pane key="layout" tab="布局">
        <div class="config-form">
          <a-form layout="vertical" size="small">
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="X坐标">
                  <a-input-number v-model:value="form.layout_x" :min="0" :max="11" style="width:100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="Y坐标">
                  <a-input-number v-model:value="form.layout_y" :min="0" style="width:100%" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="宽度">
                  <a-input-number v-model:value="form.layout_w" :min="1" :max="12" style="width:100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="高度">
                  <a-input-number v-model:value="form.layout_h" :min="1" style="width:100%" />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </div>
      </a-tab-pane>
      <a-tab-pane key="data" tab="数据">
        <div class="config-form">
          <a-form layout="vertical" size="small">
            <a-form-item label="数据源">
              <a-select v-model:value="form.datasource_id" placeholder="选择数据源" disabled>
                <a-select-option :value="dashboard?.datasource_id">
                  {{ dashboard?.datasource_id || '默认数据源' }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="SQL查询">
              <a-textarea
                v-model:value="form.sql_text"
                placeholder="输入SQL查询语句..."
                :rows="5"
                class="sql-editor"
              />
              <div class="sql-actions">
                <a-button size="small" type="primary" ghost>
                  🤖 AI生成
                </a-button>
                <a-button size="small" @click="$emit('execute-sql')">
                  测试执行
                </a-button>
              </div>
            </a-form-item>
          </a-form>
        </div>
      </a-tab-pane>
      <a-tab-pane key="advanced" tab="高级">
        <div class="config-form">
          <a-form layout="vertical" size="small">
            <a-form-item label="自动刷新间隔(秒)">
              <a-input-number v-model:value="form.refresh_interval" :min="0" style="width:100%" />
            </a-form-item>
            <a-form-item label="排序">
              <a-input-number v-model:value="form.sort_order" style="width:100%" />
            </a-form-item>
          </a-form>
        </div>
      </a-tab-pane>
    </a-tabs>

    <div class="config-footer">
      <a-button type="primary" size="small" block @click="$emit('apply', form)">
        应用配置
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { chartTypeNames, getResolvedChartType } from './chartTypeRegistry.js'

const props = defineProps({
  panel: { type: Object, default: null },
  chartData: { type: Object, default: null },
  dashboard: { type: Object, default: null },
})

defineEmits(['apply', 'execute-sql'])

const activeTab = ref('basic')

const form = ref({
  title: '',
  chartType: '',
  layout_x: 0,
  layout_y: 0,
  layout_w: 6,
  layout_h: 4,
  datasource_id: '',
  sql_text: '',
  refresh_interval: 0,
  sort_order: 0,
})

watch(
  [() => props.panel, () => props.chartData],
  ([panel, chartData]) => {
    if (panel) {
      form.value = {
        title: panel.title || '',
        chartType: getResolvedChartType(panel, chartData),
        layout_x: panel.layout_x || 0,
        layout_y: panel.layout_y || 0,
        layout_w: panel.layout_w || 6,
        layout_h: panel.layout_h || 4,
        datasource_id: props.dashboard?.datasource_id || '',
        sql_text: chartData?.sql_text || '',
        refresh_interval: 0,
        sort_order: panel.sort_order || 0,
      }
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.panel-config-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0 12px;
}

.config-form {
  padding: 8px 0;
}

.sql-editor {
  font-family: var(--font-mono);
  font-size: 12px;
}

.sql-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.config-footer {
  margin-top: auto;
  padding: 14px 0;
  border-top: 1px solid var(--color-border-light);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>