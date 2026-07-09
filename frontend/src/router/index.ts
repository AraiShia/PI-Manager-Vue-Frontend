import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/orders',
    },
    {
      path: '/orders',
      name: 'OrderSummary',
      component: () => import('@/views/order/OrderSummary.vue'),
    },
    {
      path: '/payments',
      name: 'PaymentManagement',
      component: () => import('@/views/payment/PaymentListPage.vue'),
    },
    {
      path: '/orders/:id',
      name: 'OrderSummaryDetail',
      component: () => import('@/views/order/OrderSummary.vue'),
    },
    {
      path: '/orders/:id/import',
      name: 'OrderImport',
      component: () => import('@/views/order/OrderImport.vue'),
    },
  ],
})

export default router
