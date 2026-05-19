<template>
  <div class="chat-page">
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
          <div v-else-if="msg.type === 'steps'" class="steps">
            <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="step">
              <span class="dot" :class="step.status"></span>
              <span>{{ step.text }}</span>
            </div>
          </div>

          <!-- 表格 -->
          <div v-else-if="msg.type === 'table'" class="table-wrap">
            <a-table
              :columns="msg.columns.map(c => ({ title: c, dataIndex: c, key: c }))"
              :data-source="msg.rows"
              :pagination="false"
              size="small"
              bordered
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
        placeholder="请输入您的问题，例如：查询最近7天的订单量"
        @keydown.enter.prevent="send"
      />
      <a-button
        type="primary"
        size="large"
        class="send-btn"
        :loading="loading"
        @click="send"
      >
        发送
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const question = ref('')
const messages = ref([
  {
    role: 'assistant',
    type: 'text',
    content: '您好！我是 Agent Text2SQL 智能助手。您可以向我提问关于数据仓库的任何问题，我会帮您生成 SQL 并执行查询。'
  }
])
const loading = ref(false)
const messagesEl = ref(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

const send = async () => {
  const q = question.value.trim()
  if (!q || loading.value) return

  messages.value.push({ role: 'user', type: 'text', content: q })
  question.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const res = await fetch('/api/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    })
    const data = await res.json()

    if (data.error) {
      messages.value.push({ role: 'assistant', type: 'error', content: data.error })
    } else if (data.result) {
      messages.value.push({
        role: 'assistant',
        type: 'table',
        columns: data.result.columns,
        rows: data.result.rows
      })
    } else {
      messages.value.push({ role: 'assistant', type: 'text', content: '未获取到结果' })
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', type: 'error', content: '请求失败，请稍后重试' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 112px);
  max-width: 100%;
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
