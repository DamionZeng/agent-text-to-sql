<template>
  <div class="chat-page">
    <div class="chat-topbar">
      <a-select
        v-model:value="selectedDatasource"
        placeholder="选择数据源"
        class="ds-select"
        :loading="loadingDatasources"
        @change="onDatasourceChange"
      >
        <a-select-option v-for="ds in datasources" :key="ds.id" :value="ds.id">
          {{ ds.name }}
        </a-select-option>
      </a-select>
      <span class="ds-status" :class="{ active: selectedDatasource }"></span>
    </div>

    <div ref="messagesEl" class="chat-body">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-row', msg.role, msg.type]"
      >
        <div v-if="msg.role === 'assistant'" class="ai-avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
        </div>

        <div class="bubble">
          <div v-if="msg.type === 'text'" class="text-content">{{ msg.content }}</div>

          <TaskProgressCard v-else-if="msg.type === 'steps'" :steps="msg.steps" />

          <div v-else-if="msg.type === 'table'" class="table-wrap">
            <a-table
              :columns="msg.columns.map(c => ({ title: c, dataIndex: c, key: c }))"
              :data-source="msg.rows"
              :pagination="false"
              size="small"
              bordered
            />
            <div class="msg-actions">
              <a-button size="small" type="text" :loading="msg.chartGenerating" @click="recommendChartForTable(index)">
                一键成图
              </a-button>
            </div>
          </div>

          <div v-else-if="msg.type === 'chart'" class="chart-wrap">
            <ChartRenderer
              :chart-name="msg.chartName"
              :chart-type="msg.chartType"
              :echarts-option="msg.echartsOption"
              :height="msg.height || 400"
            />
            <div class="msg-actions">
              <a-button size="small" type="text" @click="openAddToDashboard(index)">
                加入大屏
              </a-button>
            </div>
          </div>

          <div v-else-if="msg.type === 'error'" class="error-content">
            <a-alert type="error" :message="msg.content" show-icon />
          </div>
        </div>
      </div>

      <div v-if="loading" class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <div class="chat-input-area">
      <div class="input-wrapper">
        <a-textarea
          v-model:value="question"
          :rows="1"
          :auto-size="{ minRows: 1, maxRows: 5 }"
          placeholder="输入问题，例如：查询最近7天的订单量"
          :disabled="!selectedDatasource"
          @keydown.enter.exact.prevent="send"
          class="chat-textarea"
        />
        <a-button
          type="primary"
          shape="circle"
          class="send-btn"
          :loading="loading"
          :disabled="!selectedDatasource || !question.trim()"
          @click="send"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </template>
        </a-button>
      </div>
      <div class="input-hint">
        输入 <kbd>/chart</kbd> 开头可一句话生成图表
      </div>
    </div>

    <AddToDashboardModal
      :open="showAddToDashboard"
      :dashboards="dashboardList"
      :loading="addingToDashboard"
      @update:open="showAddToDashboard = $event"
      @confirm="handleAddToDashboardConfirm"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TaskProgressCard from '../../components/TaskProgressCard.vue'
import ChartRenderer from '../../components/ChartRenderer.vue'
import AddToDashboardModal from '../../components/viz/AddToDashboardModal.vue'

const question = ref('')
const router = useRouter()
const messages = ref([
  {
    role: 'assistant',
    type: 'text',
    content: '您好！我是 Agent Text2SQL 智能助手。请选择数据源后开始提问，我会帮您查询分析数据。'
  }
])
const loading = ref(false)
const loadingDatasources = ref(false)
const datasources = ref([])
const selectedDatasource = ref(null)
const messagesEl = ref(null)
const currentStepsMsg = ref(null)

const showAddToDashboard = ref(false)
const addToDashboardMsgIndex = ref(-1)
const dashboardList = ref([])
const addingToDashboard = ref(false)

const isChartCommand = (q) => q.trim().startsWith('/chart')

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
      content: `已连接数据源，可以开始提问了。`
    })
    scrollToBottom()
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

    if (!res.ok) throw new Error('请求失败')

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
        } catch (e) {}
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

    if (!res.ok) throw new Error('请求失败')

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
        } catch (e) {}
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

async function openAddToDashboard(msgIndex) {
  addToDashboardMsgIndex.value = msgIndex
  addingToDashboard.value = true
  try {
    const res = await fetch('/api/viz/dashboards?limit=50')
    if (res.ok) {
      const data = await res.json()
      dashboardList.value = data.items || []
    }
  } catch (e) {
    console.error('获取大屏列表失败', e)
  } finally {
    addingToDashboard.value = false
  }
  showAddToDashboard.value = true
}

async function handleAddToDashboardConfirm(result) {
  const msg = messages.value[addToDashboardMsgIndex.value]
  if (!msg || msg.type !== 'chart') return

  try {
    let dashboardId = null
    let panelTitle = msg.chartName || '查询图表'

    if (result.type === 'existing') {
      dashboardId = result.dashboardId
    } else if (result.type === 'new') {
      const createRes = await fetch('/api/viz/dashboards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: result.name, description: result.description, theme: 'dark' }),
      })
      if (createRes.ok) {
        const created = await createRes.json()
        dashboardId = created.id
      }
    }

    if (dashboardId) {
      await fetch(`/api/viz/dashboards/${dashboardId}/panels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: panelTitle,
          layout_x: 0,
          layout_y: 0,
          layout_w: 6,
          layout_h: 4,
        }),
      })
      router.push(`/viz/dashboards/${dashboardId}/edit`)
    }
  } catch (e) {
    console.error('加入大屏失败', e)
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 112px);
  max-width: 880px;
  margin: 0 auto;
}

/* ---------- Top Bar ---------- */
.chat-topbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.ds-select {
  flex: 1;
  max-width: 320px;
}

.ds-select :deep(.ant-select-selector) {
  border-radius: 20px !important;
  background: var(--color-bg-page) !important;
}

.ds-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-tertiary);
  transition: background 0.3s;
  flex-shrink: 0;
}

.ds-status.active {
  background: var(--color-success);
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
}

/* ---------- Messages ---------- */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  animation: messageIn 0.3s ease-out;
}

.message-row.user {
  flex-direction: row-reverse;
}

.message-row.user.steps {
  flex-direction: row;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* AI Avatar */
.ai-avatar {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

/* Bubbles */
.bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
}

.message-row.user .bubble {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-bottom-right-radius: 6px;
  box-shadow: var(--shadow-sm);
}

.message-row.assistant .bubble {
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-light);
  border-bottom-left-radius: 6px;
  box-shadow: var(--shadow-sm);
}

.message-row.assistant.steps .bubble,
.message-row.assistant.table .bubble,
.message-row.assistant.chart .bubble,
.message-row.assistant.error .bubble {
  max-width: 100%;
  padding: 16px;
  border-radius: var(--radius-lg);
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px 18px;
  width: fit-content;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: typePulse 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typePulse {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Table & Chart */
.table-wrap {
  overflow-x: auto;
}

.chart-wrap {
  width: 100%;
  min-width: 360px;
}

.msg-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border-light);
}

.error-content {
  max-width: 100%;
}

/* ---------- Input Area ---------- */
.chat-input-area {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  border-top: 1px solid var(--color-border-light);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--color-bg-surface);
  border: 2px solid var(--color-border);
  border-radius: 20px;
  padding: 6px 6px 6px 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.chat-textarea {
  flex: 1;
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
  font-size: 14px;
}

.chat-textarea:focus {
  box-shadow: none !important;
}

.send-btn {
  flex-shrink: 0;
  
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  text-align: center;
}

.input-hint kbd {
  display: inline-block;
  padding: 1px 6px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: 4px;
  border: 1px solid var(--color-primary-light);
}
</style>