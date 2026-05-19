<template>
  <a-layout style="min-height: 100vh; width: 100%;">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :width="220"
      style="background: #001529; flex-shrink: 0;"
    >
      <div class="logo">
        <span v-if="!collapsed">Agent Text2SQL</span>
        <span v-else>AI</span>
      </div>
      <a-menu
        theme="dark"
        mode="inline"
        :selectedKeys="selectedKeys"
        :openKeys="openKeys"
        @openChange="onOpenChange"
        style="border-right: none"
      >
        <a-menu-item key="chat">
          <CommentOutlined />
          <span>
            <router-link to="/chat" class="nav-link">智能问答</router-link>
          </span>
        </a-menu-item>

        <a-sub-menu key="metadata">
          <template #title>
            <span>
              <DatabaseOutlined />
              <span>元数据管理</span>
            </span>
          </template>
          <a-menu-item key="datasources">
            <span>
              <router-link to="/metadata/datasources" class="nav-link">数据源管理</router-link>
            </span>
          </a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-layout-sider>

    <a-layout style="flex: 1; min-width: 0;">
      <a-layout-header class="layout-header">
        <div class="header-title">{{ pageTitle }}</div>
      </a-layout-header>

      <a-layout-content class="layout-content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { DatabaseOutlined, CommentOutlined } from '@ant-design/icons-vue'

const collapsed = ref(false)
const route = useRoute()
const selectedKeys = ref([])
const openKeys = ref(['metadata'])

const pageTitle = computed(() => {
  if (route.path.startsWith('/chat')) {
    return '智能问答'
  }
  if (route.path.startsWith('/metadata')) {
    return '元数据管理'
  }
  return 'Agent Text2SQL'
})

const onOpenChange = (keys) => {
  openKeys.value = keys
}

watch(() => route.path, (path) => {
  if (path.startsWith('/chat')) {
    selectedKeys.value = ['chat']
  } else if (path.startsWith('/metadata/datasources')) {
    selectedKeys.value = ['datasources']
    openKeys.value = ['metadata']
  }
}, { immediate: true })
</script>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-link {
  color: inherit;
  text-decoration: none;
}

.layout-header {
  background: #fff;
  padding: 0 32px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  z-index: 10;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f1f1f;
}

.layout-content {
  margin: 0;
  padding: 24px 32px;
  background: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  min-height: calc(100vh - 112px);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}
</style>
