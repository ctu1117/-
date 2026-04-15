<template>
  <div class="page">
    <div class="profile-page">
      <section class="hero-card glass">
        <div>
          <p class="eyebrow">Profile</p>
          <h1>个人中心</h1>
          <p class="hero-copy">集中展示账号信息、累计互动数据和情绪偏好，让系统从单次体验提升为长期陪伴档案。</p>
        </div>
        <div class="profile-chip glass-subtle">
          <div class="avatar">{{ userInitial }}</div>
          <div>
            <div class="profile-name">{{ username }}</div>
            <div class="profile-subtitle">AI 情绪陪伴用户</div>
          </div>
        </div>
      </section>

      <section class="metrics-grid">
        <div class="metric-card glass">
          <span class="metric-label">累计会话</span>
          <span class="metric-value">{{ sessions.length }}</span>
        </div>
        <div class="metric-card glass">
          <span class="metric-label">累计手记</span>
          <span class="metric-value">{{ journals.length }}</span>
        </div>
        <div class="metric-card glass">
          <span class="metric-label">累计消息</span>
          <span class="metric-value">{{ totalMessages }}</span>
        </div>
        <div class="metric-card glass">
          <span class="metric-label">主导情绪</span>
          <span class="metric-value">
            {{ dominantEmotion.icon }} {{ dominantEmotion.label }}
          </span>
        </div>
      </section>

      <section class="content-grid">
        <div class="panel-card glass">
          <div class="panel-head">
            <h2>账号概览</h2>
          </div>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">用户名</span>
              <span class="info-value">{{ username }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最近活跃日期</span>
              <span class="info-value">{{ latestSessionDate }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最近一篇手记</span>
              <span class="info-value">{{ latestJournalTitle }}</span>
            </div>
          </div>
        </div>

        <div class="panel-card glass">
          <div class="panel-head">
            <h2>快捷入口</h2>
          </div>
          <div class="shortcut-list">
            <RouterLink class="shortcut-card" to="/report">
              <span class="shortcut-title">查看今日报告</span>
              <span class="shortcut-copy">回顾今天的会话、消息和手记</span>
            </RouterLink>
            <RouterLink class="shortcut-card" to="/history">
              <span class="shortcut-title">查看历史分析</span>
              <span class="shortcut-copy">快速进入折线图、分布图和会话详情</span>
            </RouterLink>
            <RouterLink class="shortcut-card" to="/journal">
              <span class="shortcut-title">继续写手记</span>
              <span class="shortcut-copy">补充主观情绪记录，形成闭环</span>
            </RouterLink>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch } from '../utils/api'
import { getEmotionMeta } from '../utils/emotions'

const sessions = ref([])
const journals = ref([])
const stats = ref({})
const username = ref(localStorage.getItem('username') || '当前用户')

onMounted(async () => {
  await Promise.all([loadSessions(), loadJournals(), loadStats()])
})

async function loadSessions() {
  const response = await apiFetch('/api/sessions')
  sessions.value = await response.json()
}

async function loadJournals() {
  const response = await apiFetch('/api/journal')
  journals.value = await response.json()
}

async function loadStats() {
  const response = await apiFetch('/api/stats')
  stats.value = await response.json()
}

const totalMessages = computed(() => sessions.value.reduce((sum, item) => sum + (item.message_count || 0), 0))

const dominantEmotion = computed(() => {
  const entries = Object.entries(stats.value || {})
  if (!entries.length) return getEmotionMeta('Neutral :|')
  const [emotion] = entries.sort((a, b) => b[1] - a[1])[0]
  return getEmotionMeta(emotion)
})

const latestSessionDate = computed(() => {
  if (!sessions.value.length) return '暂无会话记录'
  return formatDateTime(sessions.value[0].started_at)
})

const latestJournalTitle = computed(() => {
  if (!journals.value.length) return '暂无手记'
  return journals.value[0].title || '未命名手记'
})

const userInitial = computed(() => username.value.slice(0, 1).toUpperCase())

function formatDateTime(iso) {
  if (!iso) return '-'
  const date = new Date(iso)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.profile-page { max-width: 1280px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 18px; }
.hero-card { display: flex; justify-content: space-between; align-items: center; gap: 18px; padding: 28px; }
.eyebrow { color: #9ca3c6; font-size: 0.76rem; letter-spacing: 0.14em; margin-bottom: 8px; }
.hero-copy { max-width: 720px; color: var(--text-secondary); line-height: 1.8; margin-top: 10px; }
.glass-subtle { display: flex; align-items: center; gap: 14px; padding: 16px 18px; border-radius: 22px; background: rgba(255,255,255,0.05); border: 1px solid var(--border-glass); }
.avatar { width: 54px; height: 54px; border-radius: 50%; display: grid; place-items: center; background: linear-gradient(135deg, rgba(124,106,247,0.9), rgba(93,224,230,0.9)); font-weight: 700; font-size: 1.2rem; }
.profile-name { font-size: 1.05rem; font-weight: 600; }
.profile-subtitle { color: var(--text-secondary); font-size: 0.82rem; margin-top: 4px; }
.metrics-grid, .content-grid { display: grid; gap: 14px; }
.metrics-grid { grid-template-columns: repeat(4, 1fr); }
.content-grid { grid-template-columns: 1fr 1fr; }
.metric-card, .panel-card { padding: 18px; }
.metric-card { display: flex; flex-direction: column; gap: 8px; }
.metric-label, .info-label { color: var(--text-secondary); font-size: 0.8rem; }
.metric-value { font-size: 1.24rem; font-weight: 600; }
.panel-head { margin-bottom: 14px; }
.panel-head h2 { font-size: 1rem; }
.info-list, .shortcut-list { display: flex; flex-direction: column; gap: 12px; }
.info-item, .shortcut-card { padding: 14px; border-radius: 16px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); text-decoration: none; color: inherit; }
.info-item { display: flex; flex-direction: column; gap: 6px; }
.info-value, .shortcut-title { font-size: 0.96rem; font-weight: 600; }
.shortcut-copy { color: var(--text-secondary); font-size: 0.82rem; margin-top: 6px; display: block; }
@media (max-width: 1100px) {
  .hero-card,
  .metrics-grid,
  .content-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
