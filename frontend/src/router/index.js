import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import HistoryView from '../views/HistoryView.vue'

const routes = [
  { path: '/',        name: 'Chat',    component: ChatView },
  { path: '/history', name: 'History', component: HistoryView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
