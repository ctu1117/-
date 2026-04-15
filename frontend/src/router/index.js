import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import EmotionGuideView from '../views/EmotionGuideView.vue'
import HistoryView from '../views/HistoryView.vue'
import JournalDetailView from '../views/JournalDetailView.vue'
import JournalView from '../views/JournalView.vue'
import LoginView from '../views/LoginView.vue'
import ProfileView from '../views/ProfileView.vue'
import RegisterView from '../views/RegisterView.vue'
import SessionDetailView from '../views/SessionDetailView.vue'
import TodayReportView from '../views/TodayReportView.vue'

const routes = [
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/register', name: 'Register', component: RegisterView },
  { path: '/', name: 'Chat', component: ChatView, meta: { requiresAuth: true } },
  { path: '/history', name: 'History', component: HistoryView, meta: { requiresAuth: true } },
  { path: '/report', name: 'Report', component: TodayReportView, meta: { requiresAuth: true } },
  { path: '/journal', name: 'Journal', component: JournalView, meta: { requiresAuth: true } },
  { path: '/journal/:id', name: 'JournalDetail', component: JournalDetailView, meta: { requiresAuth: true } },
  { path: '/session/:id', name: 'SessionDetail', component: SessionDetailView, meta: { requiresAuth: true } },
  { path: '/profile', name: 'Profile', component: ProfileView, meta: { requiresAuth: true } },
  { path: '/emotion-guide', name: 'EmotionGuide', component: EmotionGuideView, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
