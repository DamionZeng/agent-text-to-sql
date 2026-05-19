import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layouts/MainLayout.vue'
import DatasourceList from '../views/datasource/DatasourceList.vue'
import DatasourceDetail from '../views/datasource/DatasourceDetail.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        redirect: '/datasources'
      },
      {
        path: 'datasources',
        name: 'DatasourceList',
        component: DatasourceList
      },
      {
        path: 'datasources/:id',
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
