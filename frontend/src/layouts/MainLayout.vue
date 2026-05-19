<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :width="220"
      style="background: #001529"
    >
      <div class="logo">
        <span v-if="!collapsed">元数据管理</span>
        <span v-else>MD</span>
      </div>
      <a-menu
        theme="dark"
        mode="inline"
        :selectedKeys="selectedKeys"
        style="border-right: none"
      >
        <a-menu-item key="datasources">
          <DatabaseOutlined />
          <span>
            <router-link to="/datasources" class="nav-link">数据源管理</router-link>
          </span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="layout-header">
        <div class="header-title">Agent Text2SQL - 元数据管理系统</div>
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
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { DatabaseOutlined } from '@ant-design/icons-vue'

const collapsed = ref(false)
const route = useRoute()
const selectedKeys = ref([])

watch(() => route.path, (path) => {
  if (path.startsWith('/datasources')) {
    selectedKeys.value = ['datasources']
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
