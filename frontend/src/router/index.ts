import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken, verifyToken } from '@/api'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { requiresAuth: true },
      redirect: '/admin/video',
      children: [
        {
          path: 'video',
          name: 'AdminVideo',
          component: () => import('@/views/admin/VideoView.vue')
        },
        {
          path: 'cameras',
          name: 'AdminCameras',
          component: () => import('@/views/admin/CameraView.vue')
        },
        {
          path: 'alerts',
          name: 'AdminAlerts',
          component: () => import('@/views/admin/AlertsView.vue')
        },
        {
          path: 'rag',
          name: 'AdminRag',
          component: () => import('@/views/admin/RagView.vue')
        },
        {
          path: 'sos',
          name: 'AdminSos',
          component: () => import('@/views/admin/SosView.vue')
        }
      ]
    }
  ]
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const token = getToken()
  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  try {
    await verifyToken()
  } catch {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
