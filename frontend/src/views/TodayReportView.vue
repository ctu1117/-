<template>
  <div class="page">
    <div class="report-page">
      <section class="hero-card glass">
        <div class="hero-copy">
          <p class="eyebrow">Daily Report</p>
          <h1>今日情绪报告</h1>
          <p class="hero-text">
            把今天的情绪活动、陪伴对话和手记记录集中展示，方便你在一天结束前快速回看自己的状态。
          </p>
        </div>
        <div class="hero-emotion" :class="getEmotionMeta(report.dominant_emotion || 'Neutral :|').chipStyle">
          <span class="hero-emoji">{{ getEmotionMeta(report.dominant_emotion || 'Neutral :|').icon }}</span>
          <div>
            <div class="hero-label">今日主导情绪</div>
            <div class="hero-value">{{ getEmotionMeta(report.dominant_emotion || 'Neutral :|').label }}</div>
          </div>
        </div>
      </section>

      <section class="metrics-grid">
        <div class="metric-card glass">
          <span class="metric-icon">🗓️</span>
          <span class="metric-value">{{ report.date || '--' }}</span>
          <span class="metric-label">统计日期</span>
        </div>
        <div class="metric-card glass">
          <span class="metric-icon">💬</span>
          <span class="metric-value">{{ report.session_count ?? 0 }}</span>
          <span class="metric-label">今日会话数</span>
        </div>
        <div class="metric-card glass">
          <span class="metric-icon">📝</span>
          <span class="metric-value">{{ report.journal_count ?? 0 }}</span>
          <span class="metric-label">今日手记数</span>
        </div>
        <div class="metric-card glass">
          <span class="metric-icon">📨</span>
          <span class="metric-value">{{ report.message_count ?? 0 }}</span>
          <span class="metric-label">今日消息数</span>
        </div>
      </section>

      <section class="content-grid">
        <div class="panel-card glass">
          <div class="panel-head">
            <h2>今日会话概览</h2>
            <span>{{ todaySessions.length }} 场会话</span>
          </div>
          <div v-if="todaySessions.length === 0" class="empty-state">今天还没有开始会话。</div>
          <div v-else class="session-list">
            <div v-for="session in todaySessions" :key="session.id" class="session-row">
              <div>
                <div class="session-title">
                  {{ getEmotionMeta(session.dominant_emotion).icon }} {{ getEmotionMeta(session.dominant_emotion).label }}
                </div>
                <div class="session-meta">{{ formatDateTime(session.started_at) }}</div>
              </div>
              <div class="session-extra">
                <span>{{ session.message_count }} 条消息</span>
                <RouterLink class="session-link" :to="`/session/${session.id}`">查看详情</RouterLink>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-card glass">
          <div class="panel-head">
            <h2>今日手记摘要</h2>
            <span>{{ todayJournals.length }} 篇</span>
          </div>
          <div v-if="todayJournals.length === 0" class="empty-state">今天还没有写手记。</div>
          <div v-else class="journal-list">
            <div v-for="entry in todayJournals" :key="entry.id" class="journal-row">
              <div class="journal-top">
                <span>{{ getEmotionMeta(entry.emotion).icon }} {{ getEmotionMeta(entry.emotion).label }}</span>
                <span>{{ formatDateTime(entry.created_at) }}</span>
              </div>
              <div class="journal-title">{{ entry.title || '未命名手记' }}</div>
              <div class="journal-content">{{ entry.content }}</div>
              <RouterLink class="session-link" :to="`/journal/${entry.id}`">查看详情</RouterLink>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiFetch } from '../utils/api'
import { getEmotionMeta } from '../utils/emotions'

const report = reactive({})
const todaySessions = ref([])
const todayJournals = ref([])

onMounted(async () => {
  await Promise.all([loadReport(), loadTodaySessions(), loadTodayJournals()])
})

async function loadReport() {
  const response = await apiFetch('/api/reports/today')
  const data = await response.json()
  Object.keys(report).forEach((key) => delete report[key])
  Object.assign(report, data)
}

async function loadTodaySessions() {
  const response = await apiFetch('/api/sessions')
  const data = await response.json()
  todaySessions.value = data.filter((session) => isToday(session.started_at))
}

async function loadTodayJournals() {
  const response = await apiFetch('/api/journal')
  const data = await response.json()
  todayJournals.value = data.filter((entry) => isToday(entry.created_at))
}

function isToday(iso) {
  const date = new Date(iso)
  const now = new Date()
  return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate()
}

function formatDateTime(iso) {
  const date = new Date(iso)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.report-page { max-width: 1280px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 18px; }
.hero-card { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 28px; }
.eyebrow { color: #9ca3c6; font-size: 0.76rem; letter-spacing: 0.14em; margin-bottom: 8px; }
.hero-copy h1 { font-size: 2rem; margin-bottom: 10px; }
.hero-text { max-width: 720px; color: var(--text-secondary); line-height: 1.8; }
.hero-emotion { min-width: 220px; display: flex; align-items: center; gap: 14px; padding: 18px; border-radius: 22px; background: rgba(255, 255, 255, 0.06); }
.hero-emoji { font-size: 2rem; }
.hero-label { color: var(--text-secondary); font-size: 0.82rem; }
.hero-value { font-size: 1.1rem; font-weight: 600; margin-top: 4px; }
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.metric-card { padding: 18px; display: flex; flex-direction: column; gap: 8px; }
.metric-icon { font-size: 1.4rem; }
.metric-value { font-size: 1.3rem; font-weight: 600; }
.metric-label { color: var(--text-secondary); font-size: 0.8rem; }
.content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.panel-card { padding: 18px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
.panel-head h2 { font-size: 1rem; }
.panel-head span { color: var(--text-secondary); font-size: 0.8rem; }
.empty-state { color: var(--text-secondary); padding: 28px 0; text-align: center; }
.session-list, .journal-list { display: flex; flex-direction: column; gap: 10px; }
.session-row, .journal-row { padding: 14px; border-radius: 16px; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border-glass); }
.session-title, .journal-title { font-weight: 600; margin-bottom: 4px; }
.session-meta, .journal-top, .session-extra, .journal-content { color: var(--text-secondary); font-size: 0.82rem; }
.journal-top, .session-extra { display: flex; justify-content: space-between; gap: 10px; }
.session-extra { margin-top: 6px; align-items: center; }
.session-link { color: var(--accent-1); text-decoration: none; margin-top: 8px; display: inline-block; }
.journal-content { margin-top: 6px; line-height: 1.7; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.emotion-happy { background: rgba(247, 201, 72, 0.14); color: #f7d970; }
.emotion-neutral { background: rgba(125, 211, 199, 0.14); color: #9ae6d7; }
.emotion-sad { background: rgba(110, 168, 247, 0.14); color: #8dbcf9; }
.emotion-angry { background: rgba(247, 124, 106, 0.14); color: #ffb1a4; }
.emotion-surprise { background: rgba(167, 139, 250, 0.14); color: #c4afff; }
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
