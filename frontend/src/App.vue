<template>
  <div class="bg-orbs" aria-hidden="true">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
  </div>

  <nav class="nav-bar">
    <div class="nav-logo">
      <span class="logo-icon">AI</span>
      <span>情绪感知 <span class="gradient-text">AI 伴侣</span></span>
    </div>
    <div class="nav-links">
      <RouterLink class="nav-link" to="/">对话</RouterLink>
      <RouterLink class="nav-link" to="/history">历史分析</RouterLink>
      <RouterLink class="nav-link" to="/journal">情绪手记</RouterLink>
      <a v-if="showLogout" href="#" class="nav-link" @click.prevent="logout">退出登录</a>
    </div>
  </nav>

  <RouterView />
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const showLogout = computed(() => route.path !== '/login' && route.path !== '/register')

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>
