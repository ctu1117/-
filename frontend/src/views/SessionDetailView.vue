<template>
  <div class="page">
    <div class="detail-page">
      <section v-if="loading" class="glass state-card">
        <p>正在加载会话详情...</p>
      </section>

      <section v-else-if="!session" class="glass state-card">
        <h1>未找到会话</h1>
        <p>这条会话可能已被删除，或者不属于当前登录用户。</p>
        <RouterLink class="btn btn-primary" to="/history">返回历史分析</RouterLink>
      </section>

      <template v-else>
        <section class="hero-card glass">
          <div>
            <p class="eyebrow">Session Detail</p>
            <h1>会话详情页</h1>
            <p class="hero-copy">
              查看本次对话的情绪变化、消息记录和关联手记，方便在答辩时完整展示一次会话的分析闭环。
            </p>
          </div>
          <div class="hero-actions">
            <div class="hero-emotion" :class="getEmotionMeta(session.dominant_emotion).chipStyle">
              <span>{{ getEmotionMeta(session.dominant_emotion).icon }}</span>
              <span>{{ getEmotionMeta(session.dominant_emotion).label }}</span>
            </div>
            <button class="btn btn-primary" @click="writeJournalForSession">为本次会话写手记</button>
          </div>
        </section>

        <section class="metrics-grid">
          <div class="metric-card glass">
            <span class="metric-label">开始时间</span>
            <span class="metric-value">{{ formatDateTime(session.started_at) }}</span>
          </div>
          <div class="metric-card glass">
            <span class="metric-label">会话时长</span>
            <span class="metric-value">{{ calcDuration(session.started_at, session.ended_at) }}</span>
          </div>
          <div class="metric-card glass">
            <span class="metric-label">消息数量</span>
            <span class="metric-value">{{ session.message_count }}</span>
          </div>
          <div class="metric-card glass">
            <span class="metric-label">关联手记</span>
            <span class="metric-value">{{ linkedJournals.length }}</span>
          </div>
        </section>

        <section class="content-grid">
          <div class="chart-card glass">
            <h2>本次会话情绪分布</h2>
            <EmotionPieChart :data="sessionEmotions" />
          </div>
          <div class="chart-card glass">
            <h2>情绪变化趋势</h2>
            <EmotionTrendChart :data="sessionTrendData" />
          </div>
        </section>

        <section class="content-grid">
          <div class="journal-card glass">
            <div class="section-head">
              <h2>关联手记</h2>
              <span>{{ linkedJournals.length }} 篇</span>
            </div>
            <div v-if="linkedJournals.length === 0" class="empty-state">这次会话还没有关联手记。</div>
            <div v-else class="journal-list">
              <article v-for="entry in linkedJournals" :key="entry.id" class="journal-item">
                <div class="journal-top">
                  <span>{{ getEmotionMeta(entry.emotion).icon }} {{ getEmotionMeta(entry.emotion).label }}</span>
                  <span>{{ formatDateTime(entry.created_at) }}</span>
                </div>
                <h3>{{ entry.title || '未命名手记' }}</h3>
                <p>{{ entry.content }}</p>
              </article>
            </div>
          </div>

          <div class="message-card glass">
            <div class="section-head">
              <h2>聊天记录回顾</h2>
              <RouterLink class="section-link" to="/history">返回历史分析</RouterLink>
            </div>
            <div v-if="sessionMessages.length === 0" class="empty-state">这次会话暂时没有聊天记录。</div>
            <div v-else class="message-list">
              <div
                v-for="(message, index) in sessionMessages"
                :key="index"
                class="message-row"
                :class="message.role === 'user' ? 'message-user' : 'message-ai'"
              >
                <div class="message-meta">
                  <span>{{ message.role === 'user' ? '你' : 'AI 伴侣' }}</span>
                  <span>{{ getEmotionMeta(message.emotion_at_time).icon }} {{ getEmotionMeta(message.emotion_at_time).label }}</span>
                  <span>{{ formatClock(message.timestamp) }}</span>
                </div>
                <div class="message-bubble">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import EmotionPieChart from '../components/EmotionPieChart.vue'
import EmotionTrendChart from '../components/EmotionTrendChart.vue'
import { apiFetch } from '../utils/api'
import { getEmotionMeta } from '../utils/emotions'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const session = ref(null)
const linkedJournals = ref([])
const sessionMessages = reactive([])
const sessionTrendData = reactive([])
const sessionEmotions = reactive({})

onMounted(loadSessionDetail)
watch(() => route.params.id, loadSessionDetail)

async function loadSessionDetail() {
  loading.value = true
  try {
    const sessionId = Number(route.params.id)
    const [sessionsResponse, emotionsResponse, trendResponse, messagesResponse, journalsResponse] = await Promise.all([
      apiFetch('/api/sessions'),
      apiFetch(`/api/session/${sessionId}/emotions`),
      apiFetch(`/api/session/${sessionId}/trend`),
      apiFetch(`/api/session/${sessionId}/messages`),
      apiFetch('/api/journal'),
    ])

    const sessionsData = await sessionsResponse.json()
    session.value = sessionsData.find((item) => item.id === sessionId) ?? null

    const emotionsData = await emotionsResponse.json()
    Object.keys(sessionEmotions).forEach((key) => delete sessionEmotions[key])
    Object.assign(sessionEmotions, emotionsData)

    const trendData = await trendResponse.json()
    sessionTrendData.splice(0, sessionTrendData.length, ...trendData)

    const messagesData = await messagesResponse.json()
    sessionMessages.splice(0, sessionMessages.length, ...messagesData)

    const journalsData = await journalsResponse.json()
    linkedJournals.value = journalsData.filter((entry) => entry.session_id === sessionId)
  } finally {
    loading.value = false
  }
}

function writeJournalForSession() {
  if (!session.value) return
  router.push({
    path: '/journal',
    query: {
      session_id: String(session.value.id),
      emotion: session.value.dominant_emotion,
    },
  })
}

function formatDateTime(iso) {
  if (!iso) return '-'
  const date = new Date(iso)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function formatClock(iso) {
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
.detail-page { max-width: 1320px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.state-card { padding: 32px; text-align: center; display: flex; flex-direction: column; gap: 12px; align-items: center; }
.hero-card { display: flex; justify-content: space-between; gap: 18px; padding: 26px; }
.eyebrow { color: #9ca3c6; font-size: 0.76rem; letter-spacing: 0.14em; margin-bottom: 8px; }
.hero-copy { max-width: 760px; color: var(--text-secondary); line-height: 1.8; margin-top: 10px; }
.hero-actions { display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end; gap: 12px; }
.hero-emotion { display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 999px; }
.metrics-grid, .content-grid { display: grid; gap: 14px; }
.metrics-grid { grid-template-columns: repeat(4, 1fr); }
.content-grid { grid-template-columns: 1fr 1fr; }
.metric-card, .chart-card, .journal-card, .message-card { padding: 18px; }
.metric-card { display: flex; flex-direction: column; gap: 8px; }
.metric-label { color: var(--text-secondary); font-size: 0.8rem; }
.metric-value { font-size: 1.18rem; font-weight: 600; }
.chart-card h2, .section-head h2 { font-size: 1rem; margin-bottom: 12px; }
.section-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; }
.section-link { color: var(--accent-1); text-decoration: none; font-size: 0.82rem; }
.empty-state { padding: 24px 0; text-align: center; color: var(--text-secondary); }
.journal-list, .message-list { display: flex; flex-direction: column; gap: 12px; }
.journal-item { padding: 14px; border-radius: 16px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); }
.journal-top, .message-meta { display: flex; justify-content: space-between; gap: 10px; color: var(--text-secondary); font-size: 0.78rem; }
.journal-item h3 { margin: 8px 0 6px; font-size: 0.95rem; }
.journal-item p { color: var(--text-secondary); line-height: 1.75; white-space: pre-wrap; }
.message-row { display: flex; flex-direction: column; gap: 6px; }
.message-bubble { padding: 10px 14px; border-radius: 16px; line-height: 1.65; word-break: break-word; }
.message-user .message-bubble { background: rgba(124,106,247,0.15); border: 1px solid rgba(124,106,247,0.22); align-self: flex-end; max-width: 82%; }
.message-ai .message-bubble { background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); max-width: 92%; }
.emotion-happy { background: rgba(247,201,72,0.14); color: #f7d970; }
.emotion-neutral { background: rgba(125,211,199,0.14); color: #9ae6d7; }
.emotion-sad { background: rgba(110,168,247,0.14); color: #8dbcf9; }
.emotion-angry { background: rgba(247,124,106,0.14); color: #ffb1a4; }
.emotion-surprise { background: rgba(167,139,250,0.14); color: #c4afff; }
@media (max-width: 1100px) {
  .hero-card,
  .metrics-grid,
  .content-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
  .hero-actions {
    align-items: flex-start;
  }
}
</style>
