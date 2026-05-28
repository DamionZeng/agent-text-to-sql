import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layouts/MainLayout.vue'
import DatasourceList from '../views/datasource/DatasourceList.vue'
import DatasourceDetail from '../views/datasource/DatasourceDetail.vue'
import ChatPage from '../views/chat/ChatPage.vue'
import DashboardList from '../views/viz_v2/DashboardList.vue'
import DashboardEditor from '../views/viz_v2/DashboardEditor.vue'
import DashboardView from '../views/viz_v2/DashboardView.vue'
import DatasetList from '../views/dataset/DatasetList.vue'
import DatasetEditor from '../views/dataset/DatasetEditor.vue'
import DataScreenList from '../views/viz_v2/DataScreenList.vue'
import DataScreenEditor from '../views/viz_v2/DataScreenEditor.vue'

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
      },
      {
        path: 'dataset/list',
        name: 'DatasetList',
        component: DatasetList
      },
      {
        path: 'dataset/create',
        name: 'DatasetCreate',
        component: DatasetEditor
      },
      {
        path: 'dataset/edit/:id',
        name: 'DatasetEdit',
        component: DatasetEditor
      },
      {
        path: 'viz/dashboards',
        name: 'DashboardList',
        component: DashboardList
      },
      {
        path: 'viz/data-screens',
        name: 'DataScreenList',
        component: DataScreenList
      }
    ]
  },
  {
    path: '/viz/dashboards/:id/edit',
    name: 'DashboardEditor',
    component: DashboardEditor
  },
  {
    path: '/viz/dashboards/:id/view',
    name: 'DashboardView',
    component: DashboardView
  },
  {
    path: '/viz/data-screens/:id/edit',
    name: 'DataScreenEditor',
    component: DataScreenEditor
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
