<template>
  <!-- 动态背景光球 -->
  <div class="bg-orbs" aria-hidden="true">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
  </div>

  <!-- 顶部导航 -->
  <nav class="nav-bar">
    <div class="nav-logo">
      <span class="logo-icon">🧠</span>
      <span>情绪感知 <span class="gradient-text">AI 伴侣</span></span>
    </div>
    <div class="nav-links">
      <RouterLink class="nav-link" to="/">💬 对话</RouterLink>
      <RouterLink class="nav-link" to="/history">📊 历史分析</RouterLink>
    </div>
  </nav>

  <!-- 页面路由出口 -->
  <RouterView />
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>
