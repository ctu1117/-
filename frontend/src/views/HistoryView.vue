<template>
  <div class="page">
    <div class="history-layout">
      <aside class="session-list glass">
        <div class="list-header">
          <h2>历史会话</h2>
          <span class="session-count">{{ sessions.length }} 场</span>
        </div>

        <div v-if="loading" class="list-loading">正在加载...</div>
        <div v-else-if="sessions.length === 0" class="list-empty">
          <p>暂无历史记录</p>
          <p class="hint">先去对话页体验一次情绪陪伴吧。</p>
        </div>

        <div v-else class="session-items">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: selectedId === session.id }"
            @click="selectSession(session)"
          >
            <div class="session-item-top">
              <span class="session-emotion">{{ getEmotionMeta(session.dominant_emotion).icon }}</span>
              <span class="session-date">{{ formatDate(session.started_at) }}</span>
              <button class="btn-delete" title="删除" @click.stop="deleteSession(session.id)">×</button>
            </div>
            <div class="session-item-bottom">
              <span>{{ session.message_count }} 条消息</span>
              <span>{{ calcDuration(session.started_at, session.ended_at) }}</span>
            </div>
            <div class="session-tags">
              <span v-if="session.journal_count > 0" class="session-tag">已写手记</span>
              <RouterLink class="detail-link" :to="`/session/${session.id}`" @click.stop>详情页</RouterLink>
            </div>
          </div>
        </div>
      </aside>

      <main class="analysis-panel">
        <section class="report-card glass">
          <div class="report-head">
            <div>
              <h3>今日情绪报告</h3>
              <p>{{ todayReport.date || '今日' }}</p>
            </div>
            <span class="report-emotion">
              {{ getEmotionMeta(todayReport.dominant_emotion || 'Neutral :|').icon }}
              {{ getEmotionMeta(todayReport.dominant_emotion || 'Neutral :|').label }}
            </span>
          </div>
          <div class="report-metrics">
            <div class="metric">
              <span class="metric-value">{{ todayReport.session_count ?? 0 }}</span>
              <span class="metric-label">今日会话</span>
            </div>
            <div class="metric">
              <span class="metric-value">{{ todayReport.message_count ?? 0 }}</span>
              <span class="metric-label">今日消息</span>
            </div>
            <div class="metric">
              <span class="metric-value">{{ todayReport.journal_count ?? 0 }}</span>
              <span class="metric-label">今日手记</span>
            </div>
          </div>
        </section>

        <div v-if="!selectedSession" class="empty-state glass">
          <div class="empty-icon">📊</div>
          <h3>选择一场会话查看详细分析</h3>
          <p>左侧列表支持查看每次聊天的情绪分布、趋势变化和关联手记。</p>
        </div>

        <template v-else>
          <div class="detail-header glass">
            <div>
              <h3>本次会话分析</h3>
              <p>{{ formatDate(selectedSession.started_at) }}</p>
            </div>
            <div class="detail-actions">
              <RouterLink class="btn btn-ghost" :to="`/session/${selectedSession.id}`">打开详情页</RouterLink>
              <button class="btn btn-primary" @click="writeJournalForSelectedSession">为本次会话写手记</button>
            </div>
          </div>

          <div class="stat-cards">
            <div class="stat-card glass">
              <div class="stat-icon">🗓️</div>
              <div class="stat-info">
                <div class="stat-value">{{ formatDate(selectedSession.started_at) }}</div>
                <div class="stat-label">会话时间</div>
              </div>
            </div>
            <div class="stat-card glass">
              <div class="stat-icon">💬</div>
              <div class="stat-info">
                <div class="stat-value">{{ selectedSession.message_count }}</div>
                <div class="stat-label">消息总数</div>
              </div>
            </div>
            <div class="stat-card glass">
              <div class="stat-icon">⏱️</div>
              <div class="stat-info">
                <div class="stat-value">{{ calcDuration(selectedSession.started_at, selectedSession.ended_at) }}</div>
                <div class="stat-label">持续时长</div>
              </div>
            </div>
            <div class="stat-card glass">
              <div class="stat-icon">{{ getEmotionMeta(selectedSession.dominant_emotion).icon }}</div>
              <div class="stat-info">
                <div class="stat-value">{{ getEmotionMeta(selectedSession.dominant_emotion).label }}</div>
                <div class="stat-label">主导情绪</div>
              </div>
            </div>
          </div>

          <div class="charts-row">
            <div class="chart-card glass">
              <h3 class="chart-title">本次会话情绪分布</h3>
              <EmotionPieChart :data="sessionEmotions" />
            </div>
            <div class="chart-card glass">
              <h3 class="chart-title">会话情绪折线图</h3>
              <EmotionTrendChart :data="sessionTrendData" />
            </div>
          </div>

          <div class="charts-row">
            <div class="chart-card glass">
              <h3 class="chart-title">全局情绪统计</h3>
              <EmotionPieChart :data="globalStats" />
            </div>
            <div class="chart-card glass">
              <h3 class="chart-title">关联手记</h3>
              <div v-if="linkedJournals.length === 0" class="mini-empty">本次会话还没有关联手记。</div>
              <div v-else class="journal-list">
                <div v-for="entry in linkedJournals" :key="entry.id" class="journal-item">
                  <div class="journal-item-top">
                    <span>{{ getEmotionMeta(entry.emotion).icon }} {{ getEmotionMeta(entry.emotion).label }}</span>
                    <span>{{ formatDate(entry.created_at) }}</span>
                  </div>
                  <div class="journal-item-title">{{ entry.title || '未命名手记' }}</div>
                  <div class="journal-item-content">{{ entry.content }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="messages-card glass">
            <h3 class="chart-title">聊天记录回顾</h3>
            <div class="msg-list">
              <div v-if="sessionMessages.length === 0" class="msg-empty">该会话暂时没有聊天记录。</div>
              <div
                v-for="(message, index) in sessionMessages"
                :key="index"
                class="msg-row"
                :class="message.role === 'user' ? 'msg-user' : 'msg-ai'"
              >
                <div class="msg-meta">
                  <span class="msg-role">{{ message.role === 'user' ? '你' : 'AI 伴侣' }}</span>
                  <span class="msg-emotion-tag">
                    {{ getEmotionMeta(message.emotion_at_time).icon }} {{ getEmotionMeta(message.emotion_at_time).label }}
                  </span>
                  <span class="msg-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="msg-bubble">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import EmotionPieChart from '../components/EmotionPieChart.vue'
import EmotionTrendChart from '../components/EmotionTrendChart.vue'
import { apiFetch } from '../utils/api'
import { getEmotionMeta } from '../utils/emotions'

const router = useRouter()
const sessions = reactive([])
const selectedSession = ref(null)
const selectedId = ref(null)
const loading = ref(true)

const sessionEmotions = reactive({})
const sessionMessages = reactive([])
const sessionTrendData = reactive([])
const globalStats = reactive({})
const todayReport = reactive({})
const linkedJournals = ref([])

onMounted(async () => {
  await Promise.all([loadSessions(), loadGlobalStats(), loadTodayReport()])
})

async function loadSessions() {
  loading.value = true
  try {
    const response = await apiFetch('/api/sessions')
    const data = await response.json()
    sessions.splice(0, sessions.length, ...data)
  } finally {
    loading.value = false
  }
}

async function loadGlobalStats() {
  const response = await apiFetch('/api/stats')
  const data = await response.json()
  Object.keys(globalStats).forEach((key) => delete globalStats[key])
  Object.assign(globalStats, data)
}

async function loadTodayReport() {
  const response = await apiFetch('/api/reports/today')
  const data = await response.json()
  Object.keys(todayReport).forEach((key) => delete todayReport[key])
  Object.assign(todayReport, data)
}

async function loadLinkedJournals(sessionId) {
  const response = await apiFetch('/api/journal')
  const data = await response.json()
  linkedJournals.value = data.filter((entry) => entry.session_id === sessionId)
}

async function deleteSession(sessionId) {
  if (!confirm('确认删除这次会话吗？')) return
  const response = await apiFetch(`/api/session/${sessionId}`, { method: 'DELETE' })
  if (!response.ok) return

  if (selectedId.value === sessionId) {
    selectedId.value = null
    selectedSession.value = null
    linkedJournals.value = []
    sessionTrendData.splice(0, sessionTrendData.length)
    sessionMessages.splice(0, sessionMessages.length)
    Object.keys(sessionEmotions).forEach((key) => delete sessionEmotions[key])
  }

  await Promise.all([loadSessions(), loadGlobalStats(), loadTodayReport()])
}

async function selectSession(session) {
  selectedSession.value = session
  selectedId.value = session.id

  const [emotionsResponse, trendResponse, messagesResponse] = await Promise.all([
    apiFetch(`/api/session/${session.id}/emotions`),
    apiFetch(`/api/session/${session.id}/trend`),
    apiFetch(`/api/session/${session.id}/messages`),
  ])

  const emotionsData = await emotionsResponse.json()
  Object.keys(sessionEmotions).forEach((key) => delete sessionEmotions[key])
  Object.assign(sessionEmotions, emotionsData)

  const trendData = await trendResponse.json()
  sessionTrendData.splice(0, sessionTrendData.length, ...trendData)

  const messageData = await messagesResponse.json()
  sessionMessages.splice(0, sessionMessages.length, ...messageData)

  await loadLinkedJournals(session.id)
}

function writeJournalForSelectedSession() {
  if (!selectedSession.value) return
  router.push({
    path: '/journal',
    query: {
      session_id: String(selectedSession.value.id),
      emotion: selectedSession.value.dominant_emotion,
    },
  })
}

function formatDate(iso) {
  if (!iso) return '-'
  const date = new Date(iso)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function formatTime(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

function calcDuration(start, end) {
  if (!end) return '进行中'
  const seconds = Math.floor((new Date(end) - new Date(start)) / 1000)
  if (seconds < 60) return `${seconds} 秒`
  const minutes = Math.floor(seconds / 60)
  return `${minutes} 分 ${seconds % 60} 秒`
}
</script>

<style scoped>
.history-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; padding: 16px 20px; min-height: calc(100vh - 72px); max-width: 1400px; margin: 0 auto; }
.session-list { display: flex; flex-direction: column; overflow: hidden; }
.list-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 16px 10px; border-bottom: 1px solid var(--border-glass); }
.list-header h2 { font-size: 0.95rem; font-weight: 600; }
.session-count { font-size: 0.75rem; padding: 2px 8px; background: rgba(124,106,247,0.2); border-radius: 10px; color: var(--accent-1); }
.list-loading, .list-empty { padding: 32px 16px; text-align: center; color: var(--text-secondary); font-size: 0.85rem; }
.hint { font-size: 0.78rem; margin-top: 6px; opacity: 0.7; }
.session-items { overflow-y: auto; flex: 1; padding: 8px; }
.session-item { padding: 10px 12px; border-radius: var(--radius-sm); cursor: pointer; border: 1px solid transparent; transition: all 0.18s; margin-bottom: 6px; }
.session-item:hover { background: var(--bg-glass-hover); }
.session-item.active { background: rgba(124,106,247,0.15); border-color: rgba(124,106,247,0.3); }
.session-item-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.session-emotion { font-size: 1.2rem; }
.session-date { font-size: 0.72rem; color: var(--text-secondary); flex: 1; text-align: right; }
.session-item-bottom, .session-tags { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-secondary); }
.session-tags { margin-top: 6px; align-items: center; }
.session-tag { padding: 2px 8px; border-radius: 999px; background: rgba(93,224,230,0.12); color: #8ae9ec; }
.detail-link { color: var(--accent-1); text-decoration: none; }
.btn-delete { width: 20px; height: 20px; border-radius: 50%; border: none; background: transparent; color: var(--text-secondary); font-size: 0.95rem; cursor: pointer; opacity: 0; transition: all 0.2s; }
.session-item:hover .btn-delete { opacity: 1; }
.btn-delete:hover { background: rgba(239,68,68,0.2); color: #ef4444; }
.analysis-panel { display: flex; flex-direction: column; gap: 14px; overflow-y: auto; padding-right: 4px; }
.report-card, .detail-header, .chart-card, .messages-card { padding: 16px; }
.report-head, .detail-header { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.detail-actions { display: flex; gap: 10px; }
.report-head h3, .detail-header h3 { font-size: 1rem; margin-bottom: 4px; }
.report-head p { color: var(--text-secondary); font-size: 0.78rem; }
.report-emotion { padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,0.06); }
.report-metrics, .stat-cards, .charts-row { display: grid; gap: 12px; }
.report-metrics { grid-template-columns: repeat(3, 1fr); margin-top: 18px; }
.metric, .stat-card { background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: var(--radius-md); padding: 14px; }
.metric-value, .stat-value { display: block; font-size: 1.2rem; font-weight: 600; }
.metric-label, .stat-label { display: block; font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: var(--text-secondary); padding: 40px; }
.empty-icon { font-size: 3rem; }
.empty-state h3 { font-size: 1.1rem; color: var(--text-primary); }
.stat-cards { grid-template-columns: repeat(4, 1fr); }
.stat-card { display: flex; align-items: center; gap: 12px; }
.stat-icon { font-size: 1.6rem; }
.charts-row { grid-template-columns: 1fr 1fr; }
.chart-title { font-size: 0.9rem; font-weight: 600; color: var(--text-secondary); }
.mini-empty, .msg-empty { text-align: center; color: var(--text-secondary); font-size: 0.85rem; padding: 20px; }
.journal-list { display: flex; flex-direction: column; gap: 10px; }
.journal-item { padding: 12px; border-radius: var(--radius-sm); background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); }
.journal-item-top { display: flex; justify-content: space-between; gap: 8px; font-size: 0.72rem; color: var(--text-secondary); margin-bottom: 6px; }
.journal-item-title { font-weight: 600; margin-bottom: 4px; }
.journal-item-content { color: var(--text-secondary); font-size: 0.82rem; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.msg-list { display: flex; flex-direction: column; gap: 10px; max-height: 360px; overflow-y: auto; }
.msg-row { display: flex; flex-direction: column; gap: 4px; }
.msg-meta { display: flex; align-items: center; gap: 10px; font-size: 0.72rem; color: var(--text-secondary); }
.msg-role { font-weight: 600; color: var(--text-primary); }
.msg-emotion-tag { padding: 1px 8px; background: var(--bg-glass-hover); border-radius: 10px; font-size: 0.7rem; }
.msg-time { margin-left: auto; }
.msg-bubble { padding: 8px 12px; border-radius: var(--radius-sm); font-size: 0.85rem; line-height: 1.55; word-break: break-word; }
.msg-user .msg-bubble { background: rgba(124,106,247,0.15); border: 1px solid rgba(124,106,247,0.2); align-self: flex-end; max-width: 80%; }
.msg-ai .msg-bubble { background: var(--bg-glass-hover); border: 1px solid var(--border-glass); max-width: 90%; }
@media (max-width: 1100px) { .history-layout, .report-metrics, .stat-cards, .charts-row { grid-template-columns: 1fr; } .detail-actions { flex-direction: column; width: 100%; } }
</style>
