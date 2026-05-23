<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :width="220"
      :trigger="null"
      class="app-sidebar"
    >
      <div class="logo" @click="$router.push('/')">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <polyline points="6 9 12 15 18 9"></polyline>
          <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
          <path d="M2 17l10 5 10-5"></path>
          <path d="M2 12l10 5 10-5"></path>
        </svg>
        <span v-if="!collapsed" class="logo-text">AgentText2SQL</span>
      </div>

      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        class="sidebar-menu"
        @click="onMenuClick"
      >
        <a-menu-item key="/chat">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </template>
          <span>智能对话</span>
        </a-menu-item>

        <a-menu-item key="/metadata/datasources">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
            </svg>
          </template>
          <span>数据源管理</span>
        </a-menu-item>

        <a-menu-item key="/viz/dashboards">
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
          </template>
          <span>可视化大屏</span>
        </a-menu-item>
      </a-menu>

      <div class="sidebar-footer">
        <a-button
          type="text"
          class="collapse-btn"
          @click="collapsed = !collapsed"
          :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
        >
          <template #icon>
            <MenuFoldOutlined v-if="!collapsed" />
            <MenuUnfoldOutlined v-else />
          </template>
        </a-button>
      </div>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="app-header">
        <div class="header-left">
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>
        <div class="header-right">
          <a-tag
            v-if="selectedDatasourceName"
            class="ds-tag"
          >
            <span class="tag-dot"></span>
            {{ selectedDatasourceName }}
          </a-tag>
        </div>
      </a-layout-header>

      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

const collapsed = ref(false)
const selectedKeys = ref(['/chat'])
const selectedDatasourceName = ref('')

watch(() => route.path, (path) => {
  if (path.startsWith('/viz')) {
    selectedKeys.value = ['/viz/dashboards']
  } else if (path.startsWith('/metadata')) {
    selectedKeys.value = ['/metadata/datasources']
  } else {
    selectedKeys.value = ['/chat']
  }
}, { immediate: true })

const pageTitle = computed(() => {
  if (route.path.startsWith('/viz')) return '可视化大屏'
  if (route.path.startsWith('/metadata')) return '数据源管理'
  return '智能对话'
})

const onMenuClick = ({ key }) => {
  router.push(key)
}
</script>

<style scoped>
.app-sidebar {
  background: var(--color-sidebar-bg) !important;
}

.app-sidebar :deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--color-text-inverse);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.3px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  padding: 0 16px;
}

.logo-text {
  white-space: nowrap;
  font-family: var(--font-sans);
}

.sidebar-menu {
  flex: 1;
  padding: 8px;
  background: transparent !important;
  border-inline-end: none !important;
}

.sidebar-menu :deep(.ant-menu-item) {
  margin: 2px 0;
  border-radius: var(--radius-md);
  color: var(--color-sidebar-text);
  transition: all var(--transition-normal);
  height: 40px;
  line-height: 40px;
}

.sidebar-menu :deep(.ant-menu-item:hover) {
  color: var(--color-sidebar-text-active);
  background: var(--color-sidebar-hover);
}

.sidebar-menu :deep(.ant-menu-item-selected) {
  background: var(--color-sidebar-active) !important;
  color: var(--color-sidebar-text-active) !important;
  font-weight: 500;
}

.sidebar-menu :deep(.ant-menu-item .anticon) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-footer {
  padding: 10px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.collapse-btn {
  width: 100%;
  color: var(--color-sidebar-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn:hover {
  color: var(--color-sidebar-text-active);
}

.app-header {
  height: 56px;
  background: var(--color-bg-surface);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-border-light);
  line-height: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ds-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 20px;
  padding: 2px 12px;
  font-size: 12px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border: 1px solid var(--color-primary-light);
}

.tag-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

.app-content {
  padding: 0;
  min-height: 280px;
  overflow: auto;
}

.app-content :deep(.chat-page) {
  padding: 0;
}
</style>