<template>
  <div class="datascreen-list">
    <div class="page-header">
      <div class="page-title">
        <h2>数据大屏</h2>
        <p class="page-desc">基于自由布局的自定义可视化数据大屏，支持自由拖拽与丰富样式配置</p>
      </div>
      <a-button type="primary" size="large" @click="handleCreate">
        <PlusOutlined /> 新增数据大屏
      </a-button>
    </div>

    <div class="screen-grid">
      <a-card 
        v-for="screen in screens" 
        :key="screen.id"
        hoverable 
        class="screen-card"
      >
        <template #cover>
          <div class="screen-cover" :style="getCoverStyle(screen)">
            <div class="screen-actions">
              <a-button type="primary" @click="goToEdit(screen.id)">编辑数据大屏</a-button>
            </div>
          </div>
        </template>
        <a-card-meta :title="screen.name">
          <template #description>
            <div class="meta-desc">
              <span>状态: <a-tag :color="screen.status === 'published' ? 'green' : 'default'">{{ screen.status === 'published' ? '已发布' : '草稿' }}</a-tag></span>
              <span class="time">{{ new Date(screen.updated_at).toLocaleDateString() }}</span>
            </div>
          </template>
        </a-card-meta>
      </a-card>

      <!-- Empty state when no screens -->
      <a-empty v-if="!loading && screens.length === 0" description="暂无数据大屏，点击右上角新建" style="grid-column: 1 / -1; padding: 40px;" />
    </div>

    <a-modal v-model:open="createModalVisible" title="新建数据大屏" @ok="confirmCreate" :confirmLoading="creating">
      <a-form layout="vertical">
        <a-form-item label="数据大屏名称" required>
          <a-input v-model:value="newScreen.name" placeholder="请输入数据大屏名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="newScreen.description" placeholder="请输入简要描述" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useDataScreen } from '../../composables/viz/useDataScreen'
import { message } from 'ant-design-vue'

const router = useRouter()
const { screens, loading, fetchList, createScreen } = useDataScreen()

const createModalVisible = ref(false)
const creating = ref(false)
const newScreen = reactive({ name: '', description: '' })

onMounted(() => {
  fetchList()
})

const getCoverStyle = (screen) => {
  if (screen.cover) {
    return { backgroundImage: `url(${screen.cover})`, backgroundSize: 'cover' }
  }
  return { background: '#1f2937' } // default dark background
}

const handleCreate = () => {
  newScreen.name = ''
  newScreen.description = ''
  createModalVisible.value = true
}

const confirmCreate = async () => {
  if (!newScreen.name) return message.warning('请输入大屏名称')
  creating.value = true
  try {
    const res = await createScreen({
      name: newScreen.name,
      description: newScreen.description,
      canvas_style_data: { width: 1920, height: 1080, backgroundColor: '#0f172a' }
    })
    message.success('创建成功')
    createModalVisible.value = false
    router.push(`/viz/data-screens/${res.id}/edit`)
  } catch (err) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

const goToEdit = (id) => {
  router.push(`/viz/data-screens/${id}/edit`)
}
</script>

<style scoped>
.datascreen-list {
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.page-title h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}
.page-desc {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}
.screen-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}
.screen-card {
  border-radius: 8px;
  overflow: hidden;
}
.screen-cover {
  height: 180px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.screen-cover::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  opacity: 0;
  transition: opacity 0.3s;
}
.screen-card:hover .screen-cover::after {
  opacity: 1;
}
.screen-actions {
  position: relative;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.3s;
}
.screen-card:hover .screen-actions {
  opacity: 1;
}
.meta-desc {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.time {
  font-size: 12px;
  color: #9ca3af;
}
</style>
