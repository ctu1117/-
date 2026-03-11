<template>
  <div class="page">
    <div class="history-layout">

      <!-- ── 左侧：会话列表 ── -->
      <aside class="session-list glass">
        <div class="list-header">
          <h2>📋 历史会话</h2>
          <span class="session-count">{{ sessions.length }} 次</span>
        </div>
        <div v-if="loading" class="list-loading">加载中...</div>
        <div v-else-if="sessions.length === 0" class="list-empty">
          <p>暂无历史记录</p>
          <p class="hint">先去对话页聊几句吧！</p>
        </div>
        <div v-else class="session-items">
          <div
            v-for="s in sessions"
            :key="s.id"
            class="session-item"
            :class="{ active: selectedId === s.id }"
            @click="selectSession(s)"
          >
            <div class="session-item-top">
              <span class="session-emotion">{{ getEmotionIcon(s.dominant_emotion) }}</span>
              <span class="session-date">{{ formatDate(s.started_at) }}</span>
            </div>
            <div class="session-item-bottom">
              <span class="session-msg-count">💬 {{ s.message_count }} 条消息</span>
              <span class="session-duration">{{ calcDuration(s.started_at, s.ended_at) }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- ── 右侧：分析面板 ── -->
      <main class="analysis-panel">

        <!-- 未选择时的引导 -->
        <div v-if="!selectedSession" class="empty-state glass">
          <div class="empty-icon">📊</div>
          <h3>选择一次会话查看分析</h3>
          <p>从左侧列表选取任意历史会话</p>
        </div>

        <template v-else>

          <!-- 顶部统计卡片 -->
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
              <div class="stat-icon">{{ getEmotionIcon(selectedSession.dominant_emotion) }}</div>
              <div class="stat-info">
                <div class="stat-value">{{ getEmotionLabel(selectedSession.dominant_emotion) }}</div>
                <div class="stat-label">主要情绪</div>
              </div>
            </div>
          </div>

          <!-- 中部：饼图 + 全局饼图 -->
          <div class="charts-row">
            <div class="chart-card glass">
              <h3 class="chart-title">本次情绪分布</h3>
              <EmotionPieChart :data="sessionEmotions" />
            </div>
            <div class="chart-card glass">
              <h3 class="chart-title">历史全局情绪分布</h3>
              <EmotionPieChart :data="globalStats" />
            </div>
          </div>

          <!-- 底部：聊天记录回顾 -->
          <div class="messages-card glass">
            <h3 class="chart-title">💬 聊天记录回顾</h3>
            <div class="msg-list">
              <div v-if="sessionMessages.length === 0" class="msg-empty">该会话无聊天记录</div>
              <div
                v-for="(msg, i) in sessionMessages"
                :key="i"
                class="msg-row"
                :class="msg.role === 'user' ? 'msg-user' : 'msg-ai'"
              >
                <div class="msg-meta">
                  <span class="msg-role">{{ msg.role === 'user' ? '👤 你' : '🤖 AI' }}</span>
                  <span class="msg-emotion-tag">{{ getEmotionIcon(msg.emotion_at_time) }} {{ getEmotionLabel(msg.emotion_at_time) }}</span>
                  <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
                </div>
                <div class="msg-bubble">{{ msg.content }}</div>
              </div>
            </div>
          </div>

        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import EmotionPieChart from '../components/EmotionPieChart.vue'

// ── 情绪配置 ──────────────────────────────────────────────
const EMOTION_MAP = {
  'Happy :)':   { icon: '😊', label: '开心' },
  'Angry >_<':  { icon: '😠', label: '生气' },
  'Sad  :(':    { icon: '😢', label: '伤心' },
  'Surprise!':  { icon: '😲', label: '惊讶' },
  'Neutral :|': { icon: '😐', label: '平静' },
  'No Face':    { icon: '🙈', label: '未知' },
}
const getEmotionIcon  = (e) => EMOTION_MAP[e]?.icon  ?? '😐'
const getEmotionLabel = (e) => EMOTION_MAP[e]?.label ?? e

// ── 状态 ──────────────────────────────────────────────────
const sessions = reactive([])
const selectedSession = ref(null)
const selectedId = ref(null)
const loading = ref(true)

const sessionEmotions  = reactive({})
const sessionMessages  = reactive([])
const globalStats      = reactive({})

// ── 加载会话列表 ──────────────────────────────────────────
onMounted(async () => {
  await loadSessions()
  await loadGlobalStats()
})

async function loadSessions() {
  loading.value = true
  try {
    const res = await fetch('/api/sessions')
    const data = await res.json()
    sessions.splice(0, sessions.length, ...data)
  } finally {
    loading.value = false
  }
}

async function loadGlobalStats() {
  const res = await fetch('/api/stats')
  const data = await res.json()
  Object.assign(globalStats, data)
}

async function selectSession(s) {
  selectedSession.value = s
  selectedId.value = s.id

  // 加载情绪分布
  const eRes = await fetch(`/api/session/${s.id}/emotions`)
  const eData = await eRes.json()
  Object.keys(sessionEmotions).forEach(k => delete sessionEmotions[k])
  Object.assign(sessionEmotions, eData)

  // 加载聊天记录
  const mRes = await fetch(`/api/session/${s.id}/messages`)
  const mData = await mRes.json()
  sessionMessages.splice(0, sessionMessages.length, ...mData)
}

// ── 工具函数 ──────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}
function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
}
function calcDuration(start, end) {
  if (!end) return '进行中'
  const s = Math.floor((new Date(end) - new Date(start)) / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  const r = s % 60
  return `${m}m ${r}s`
}
</script>

<style scoped>
.history-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  padding: 16px 20px;
  height: calc(100vh - 72px);
  max-width: 1400px;
  margin: 0 auto;
}

/* ── 左侧会话列表 ── */
.session-list {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 10px;
  border-bottom: 1px solid var(--border-glass);
}
.list-header h2 { font-size: 0.95rem; font-weight: 600; }
.session-count {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: rgba(124,106,247,0.2);
  border-radius: 10px;
  color: var(--accent-1);
}
.list-loading, .list-empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}
.hint { font-size: 0.78rem; margin-top: 6px; opacity: 0.7; }

.session-items { overflow-y: auto; flex: 1; padding: 8px; }
.session-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.18s;
  margin-bottom: 4px;
}
.session-item:hover { background: var(--bg-glass-hover); }
.session-item.active {
  background: rgba(124,106,247,0.15);
  border-color: rgba(124,106,247,0.3);
}
.session-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.session-emotion { font-size: 1.2rem; }
.session-date { font-size: 0.72rem; color: var(--text-secondary); }
.session-item-bottom {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: var(--text-secondary);
}

/* ── 右侧分析面板 ── */
.analysis-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  padding-right: 4px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  padding: 40px;
}
.empty-icon { font-size: 3rem; }
.empty-state h3 { font-size: 1.1rem; color: var(--text-primary); }

/* 统计卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
}
.stat-icon { font-size: 1.6rem; }
.stat-value { font-size: 1rem; font-weight: 600; }
.stat-label { font-size: 0.72rem; color: var(--text-secondary); margin-top: 2px; }

/* 图表行 */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.chart-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* 聊天记录 */
.messages-card { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.msg-list { display: flex; flex-direction: column; gap: 10px; max-height: 360px; overflow-y: auto; }
.msg-empty { text-align: center; color: var(--text-secondary); font-size: 0.85rem; padding: 20px; }

.msg-row { display: flex; flex-direction: column; gap: 4px; }
.msg-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.72rem;
  color: var(--text-secondary);
}
.msg-role { font-weight: 600; color: var(--text-primary); }
.msg-emotion-tag {
  padding: 1px 8px;
  background: var(--bg-glass-hover);
  border-radius: 10px;
  font-size: 0.7rem;
}
.msg-time { margin-left: auto; }
.msg-bubble {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  line-height: 1.55;
  word-break: break-word;
}
.msg-user .msg-bubble {
  background: rgba(124,106,247,0.15);
  border: 1px solid rgba(124,106,247,0.2);
  align-self: flex-end;
  max-width: 80%;
}
.msg-ai .msg-bubble {
  background: var(--bg-glass-hover);
  border: 1px solid var(--border-glass);
  max-width: 90%;
}
</style>
