<template>
  <div class="task-progress-card" :class="{ expanded: isExpanded, finished: isFinished }" @click="toggle">
    <!-- 折叠状态：只显示图标 + 当前任务名 -->
    <div class="task-header">
      <div class="task-icon">
        <LoadingOutlined v-if="!isFinished" class="spin" />
        <CheckCircleFilled v-else class="done-icon" />
      </div>
      <div class="task-title">{{ displayTitle }}</div>
      <div class="task-arrow">
        <RightOutlined v-if="!isExpanded" />
        <DownOutlined v-else />
      </div>
    </div>

    <!-- 展开状态：完整步骤时间线 -->
    <div v-if="isExpanded" class="task-body" @click.stop>
      <div class="timeline">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          class="timeline-item"
          :class="normalizedStepClass(step.status)"
        >
          <div class="timeline-dot">
            <CheckCircleFilled v-if="isSuccessStatus(step.status)" />
            <CloseCircleFilled v-else-if="step.status === 'error'" />
            <LoadingOutlined v-else-if="step.status === 'running'" class="spin" />
            <ClockCircleOutlined v-else />
          </div>
          <div class="timeline-content">
            <div class="step-name">{{ step.text }}</div>
            <div v-if="step.message" class="step-message">{{ step.message }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  LoadingOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  RightOutlined,
  DownOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  }
})

const isExpanded = ref(false)

const isSuccessStatus = (status) => status === 'done' || status === 'success'

const isFinished = computed(() => {
  if (!props.steps.length) return false
  return props.steps.every(s => isSuccessStatus(s.status))
})

const normalizedStepClass = (status) => {
  if (status === 'success') return 'done'
  return status
}

const displayTitle = computed(() => {
  if (!props.steps.length) return '准备中...'
  const running = props.steps.find(s => s.status === 'running')
  if (running) return running.text
  const errorStep = props.steps.find(s => s.status === 'error')
  if (errorStep) return `失败: ${errorStep.text}`
  if (isFinished.value) return '任务已完成'
  return props.steps[0]?.text || '准备中...'
})

const toggle = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
.task-progress-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
}

.task-progress-card:hover {
  border-color: #d9d9d9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.task-progress-card.finished {
  background: #f6ffed;
  border-color: #b7eb8f;
}

.task-progress-card.finished:hover {
  border-color: #52c41a;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
}

.task-icon {
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.task-icon .spin {
  color: #1677ff;
  animation: spin 1s linear infinite;
}

.task-icon .done-icon {
  color: #52c41a;
  font-size: 18px;
}

.task-title {
  flex: 1;
  font-size: 13px;
  color: #262626;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-arrow {
  font-size: 12px;
  color: #8c8c8c;
  transition: transform 0.2s;
}

.task-body {
  padding: 0 14px 14px 14px;
  border-top: 1px solid #f0f0f0;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-top: 12px;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
  padding-bottom: 16px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 22px;
  bottom: 0;
  width: 1px;
  background: #f0f0f0;
}

.timeline-item.done:not(:last-child)::before {
  background: #b7eb8f;
}

.timeline-dot {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}

.timeline-item.done .timeline-dot {
  color: #52c41a;
}

.timeline-item.error .timeline-dot {
  color: #ff4d4f;
}

.timeline-item.running .timeline-dot {
  color: #1677ff;
}

.timeline-item.running .timeline-dot .spin {
  animation: spin 1s linear infinite;
}

.timeline-item.pending .timeline-dot {
  color: #d9d9d9;
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.step-name {
  font-size: 13px;
  color: #262626;
  line-height: 1.5;
}

.timeline-item.done .step-name {
  color: #52c41a;
}

.timeline-item.error .step-name {
  color: #ff4d4f;
}

.timeline-item.running .step-name {
  color: #1677ff;
  font-weight: 500;
}

.timeline-item.pending .step-name {
  color: #8c8c8c;
}

.step-message {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
  line-height: 1.4;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
