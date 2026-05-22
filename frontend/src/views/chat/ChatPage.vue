<template>
  <div class="chat-page">
    <!-- 数据源选择区 -->
    <div class="datasource-selector">
      <a-select
        v-model:value="selectedDatasource"
        placeholder="请选择数据源"
        style="width: 100%"
        :loading="loadingDatasources"
        @change="onDatasourceChange"
      >
        <a-select-option
          v-for="ds in datasources"
          :key="ds.id"
          :value="ds.id"
        >
          {{ ds.name }} ({{ ds.type.toUpperCase() }})
        </a-select-option>
      </a-select>
      <a-tag v-if="selectedDatasource" color="green">已连接</a-tag>
    </div>

    <!-- 消息区 -->
    <div ref="messagesEl" class="messages">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-row', msg.role]"
      >
        <div v-if="msg.role === 'assistant'" class="avatar">🤖</div>

        <div class="bubble">
          <!-- 文本 -->
          <div v-if="msg.type === 'text'" class="text-content">
            {{ msg.content }}
          </div>

          <!-- 进度步骤 -->
          <TaskProgressCard
            v-else-if="msg.type === 'steps'"
            :steps="msg.steps"
          />

          <!-- 表格 -->
          <div v-else-if="msg.type === 'table'" class="table-wrap">
            <a-table
              :columns="msg.columns.map(c => ({ title: c, dataIndex: c, key: c }))"
              :data-source="msg.rows"
              :pagination="false"
              size="small"
              bordered
            />
            <div class="table-actions">
              <a-button
                size="small"
                type="dashed"
                :loading="msg.chartGenerating"
                @click="recommendChartForTable(index)"
              >
                📊 一键成图
              </a-button>
            </div>
          </div>

          <!-- 图表 -->
          <div v-else-if="msg.type === 'chart'" class="chart-wrap">
            <ChartRenderer
              :chart-name="msg.chartName"
              :chart-type="msg.chartType"
              :echarts-option="msg.echartsOption"
              :height="msg.height || 400"
            />
          </div>

          <!-- 错误 -->
          <div v-else-if="msg.type === 'error'" class="error-text">
            <a-alert type="error" :message="msg.content" show-icon />
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <a-textarea
        v-model:value="question"
        :rows="3"
        placeholder="请输入您的问题，例如：查询最近7天的订单量。输入 /chart 开头可一句话生成图表"
        :disabled="!selectedDatasource"
        @keydown.enter.prevent="send"
      />
      <a-button
        type="primary"
        size="large"
        class="send-btn"
        :loading="loading"
        :disabled="!selectedDatasource"
        @click="send"
      >
        发送
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import TaskProgressCard from '../../components/TaskProgressCard.vue'
import ChartRenderer from '../../components/ChartRenderer.vue'

const question = ref('')
const messages = ref([
  {
    role: 'assistant',
    type: 'text',
    content: '您好！我是 Agent Text2SQL 智能助手。请先选择数据源，然后向我提问关于数据仓库的任何问题，我会帮您生成 SQL 并执行查询。\n\n💡 使用 /chart 开头可以一句话生成图表，例如：/chart 做一个最近7天的销售趋势图和品类占比图'
  }
])
const loading = ref(false)
const loadingDatasources = ref(false)
const datasources = ref([])
const selectedDatasource = ref(null)
const messagesEl = ref(null)
const currentStepsMsg = ref(null)

const isChartCommand = (q) => {
  return q.trim().startsWith('/chart')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

const fetchDatasources = async () => {
  loadingDatasources.value = true
  try {
    const res = await fetch('/api/metadata/datasources')
    if (res.ok) {
      datasources.value = await res.json()
    }
  } catch (e) {
    console.error('获取数据源失败', e)
  } finally {
    loadingDatasources.value = false
  }
}

const onDatasourceChange = () => {
  if (selectedDatasource.value) {
    messages.value.push({
      role: 'assistant',
      type: 'text',
      content: `已选择数据源！现在您可以开始提问了。`
    })
  }
}

const send = async () => {
  const q = question.value.trim()
  if (!q || loading.value || !selectedDatasource.value) return

  const chartMode = isChartCommand(q)
  const queryText = chartMode ? q.replace(/^\/chart\s*/, '') : q

  messages.value.push({ role: 'user', type: 'text', content: q })
  question.value = ''
  loading.value = true

  currentStepsMsg.value = {
    role: 'assistant',
    type: 'steps',
    steps: []
  }
  messages.value.push(currentStepsMsg.value)
  scrollToBottom()

  try {
    const endpoint = chartMode ? '/api/viz/charts/generate' : '/api/query'
    const body = chartMode
      ? { query: queryText, datasource_id: selectedDatasource.value }
      : { query: q, datasource_id: selectedDatasource.value }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    if (!res.ok) {
      throw new Error('请求失败')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const evt of events) {
        const line = evt.trim()
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.replace(/^data:\s*/, ''))
          if (chartMode) {
            handleChartSSEEvent(data)
          } else {
            handleSSEEvent(data)
          }
        } catch (e) {
          // ignore invalid JSON
        }
      }
    }

  } catch (e) {
    messages.value.push({
      role: 'assistant',
      type: 'error',
      content: `请求失败：${e.message || '未知错误'}`
    })
  } finally {
    loading.value = false
    currentStepsMsg.value = null
    scrollToBottom()
  }
}

const handleSSEEvent = (data) => {
  if (data.type === 'progress') {
    if (currentStepsMsg.value) {
      const steps = currentStepsMsg.value.steps
      let step = steps.find((s) => s.text === data.step)

      if (!step) {
        step = { text: data.step, status: data.status }
        steps.push(step)
      } else {
        step.status = data.status
      }
    }
  } else if (data.type === 'result' && Array.isArray(data.data)) {
    messages.value.push({
      role: 'assistant',
      type: 'table',
      columns: Object.keys(data.data[0] || {}),
      rows: data.data,
      chartGenerating: false,
    })
  }
}

const handleChartSSEEvent = (data) => {
  if (data.type === 'progress') {
    if (currentStepsMsg.value) {
      const steps = currentStepsMsg.value.steps
      let step = steps.find((s) => s.text === data.step)

      if (!step) {
        step = { text: data.step, status: data.status }
        steps.push(step)
      } else {
        step.status = data.status
      }
    }
  } else if (data.type === 'chart_results' && Array.isArray(data.charts)) {
    for (const chart of data.charts) {
      messages.value.push({
        role: 'assistant',
        type: 'chart',
        chartName: chart.chart_name || '图表',
        chartType: chart.chart_type || 'bar',
        echartsOption: chart.echarts_option || {},
        height: 400,
      })
    }
  } else if (data.type === 'chart_plans') {
    // plans received, will be followed by chart_results
  } else if (data.type === 'error') {
    messages.value.push({
      role: 'assistant',
      type: 'error',
      content: data.message || '生成图表失败'
    })
  }
}

const recommendChartForTable = async (msgIndex) => {
  const msg = messages.value[msgIndex]
  if (!msg || msg.type !== 'table' || !msg.rows || msg.rows.length === 0) return

  msg.chartGenerating = true

  try {
    const res = await fetch('/api/viz/charts/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        datasource_id: selectedDatasource.value,
        sql: '',
        query_result: msg.rows,
      })
    })

    if (!res.ok) {
      throw new Error('请求失败')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const evt of events) {
        const line = evt.trim()
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.replace(/^data:\s*/, ''))
          if (data.type === 'chart_result') {
            messages.value.push({
              role: 'assistant',
              type: 'chart',
              chartName: data.chart_name || '图表',
              chartType: data.chart_type || 'bar',
              echartsOption: data.echarts_option || {},
              height: 400,
            })
          }
        } catch (e) {
          // ignore
        }
      }
    }
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      type: 'error',
      content: `生成图表失败：${e.message || '未知错误'}`
    })
  } finally {
    msg.chartGenerating = false
  }
}

onMounted(() => {
  fetchDatasources()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 112px);
  max-width: 100%;
}

.datasource-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 16px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.message-row.user .bubble {
  background: #1677ff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .bubble {
  background: #f5f5f5;
  color: #1f1f1f;
  border-bottom-left-radius: 4px;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.dot.pending {
  background: #d9d9d9;
}

.dot.running {
  background: #1677ff;
  animation: pulse 1.5s infinite;
}

.dot.done {
  background: #52c41a;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

.table-wrap {
  overflow-x: auto;
}

.table-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.chart-wrap {
  width: 100%;
  min-width: 400px;
}

.error-text {
  color: #cf1322;
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 16px 0 0 0;
  border-top: 1px solid #f0f0f0;
}

.input-area :deep(.ant-input) {
  resize: none;
}

.send-btn {
  flex-shrink: 0;
  align-self: flex-end;
}
</style>
