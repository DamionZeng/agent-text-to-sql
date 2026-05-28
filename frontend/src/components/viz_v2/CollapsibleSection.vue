<template>
  <div class="collapsible-section" :class="{ 'is-collapsed': !isExpanded }">
    <div class="section-header" @click="toggle">
      <div class="header-left">
        <slot name="icon">
          <AppstoreOutlined v-if="title === '组件库'" class="header-icon" />
          <ContainerOutlined v-else-if="title === '图层管理'" class="header-icon" />
          <BlockOutlined v-else class="header-icon" />
        </slot>
        <span class="header-title">{{ title }}</span>
        <a-badge v-if="badgeCount !== undefined" :count="badgeCount" :overflow-count="99" class="header-badge" />
      </div>
      <div class="header-right">
        <RightOutlined class="toggle-arrow" />
      </div>
    </div>
    <Transition name="collapse">
      <div v-show="isExpanded" class="section-body">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { RightOutlined, AppstoreOutlined, ContainerOutlined, BlockOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  title: { type: String, required: true },
  defaultExpanded: { type: Boolean, default: true },
  badgeCount: { type: Number, default: undefined },
})

const isExpanded = ref(props.defaultExpanded)

watch(() => props.defaultExpanded, (val) => {
  isExpanded.value = val
})

function toggle() {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
.collapsible-section {
  border-bottom: 1px solid var(--color-border-light);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}
.section-header:hover {
  background: rgba(0, 0, 0, 0.03);
}
.dark-theme .section-header:hover {
  background: rgba(255, 255, 255, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-icon {
  font-size: 14px;
  color: var(--color-text-tertiary);
}
.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.dark-theme .header-title {
  color: rgba(255, 255, 255, 0.85);
}
.header-badge {
  margin-left: 4px;
}

.toggle-arrow {
  font-size: 11px;
  color: var(--color-text-tertiary);
  transition: transform 0.2s ease;
}
.collapsible-section.is-collapsed .toggle-arrow {
  transform: rotate(0deg);
}
.collapsible-section:not(.is-collapsed) .toggle-arrow {
  transform: rotate(90deg);
}

.section-body {
  padding: 0 12px 12px 14px;
  overflow: hidden;
}

/* Collapse transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
}
.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
