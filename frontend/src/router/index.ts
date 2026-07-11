import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { BUSINESS_ROUTES } from './businessRoutes'

const implementedRoutes: RouteRecordRaw[] = [
  { path: '/products', name: 'Products', component: () => import('@/views/product/ProductManagement.vue') },
  { path: '/orders', name: 'OrderSummary', component: () => import('@/views/order/OrderSummary.vue') },
  { path: '/orders/:id', name: 'OrderSummaryDetail', component: () => import('@/views/order/OrderSummary.vue') },
  { path: '/orders/:id/import', name: 'OrderImport', component: () => import('@/views/order/OrderImport.vue') },
  { path: '/shipments', name: 'Shipments', component: () => import('@/views/shipment/ShipmentsPage.vue') },
  { path: '/payments', redirect: '/payments/customer' },
  { path: '/payments/customer', name: 'CustomerPayments', component: () => import('@/views/payment/PaymentListPage.vue') },
]

const placeholderRoutes: RouteRecordRaw[] = BUSINESS_ROUTES
  .filter(item => !item.implemented)
  .map(item => ({
    path: item.path,
    name: `ComingSoon-${item.key}`,
    component: () => import('@/views/misc/ComingSoonView.vue'),
    meta: { title: item.title, source: item.source, owner: item.owner },
  }))

const fallbackRoute: RouteRecordRaw = {
  path: '/:pathMatch(.*)*',
  name: 'ComingSoonFallback',
  component: () => import('@/views/misc/ComingSoonView.vue'),
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/orders' },
    ...implementedRoutes,
    ...placeholderRoutes,
    fallbackRoute,
  ],
})

export default router
