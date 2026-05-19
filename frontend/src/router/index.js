import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layouts/MainLayout.vue'
import DatasourceList from '../views/datasource/DatasourceList.vue'
import DatasourceDetail from '../views/datasource/DatasourceDetail.vue'
import ChatPage from '../views/chat/ChatPage.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: ChatPage
      },
      {
        path: 'metadata',
        redirect: '/metadata/datasources'
      },
      {
        path: 'metadata/datasources',
        name: 'DatasourceList',
        component: DatasourceList
      },
      {
        path: 'metadata/datasources/:id',
        name: 'DatasourceDetail',
        component: DatasourceDetail
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
