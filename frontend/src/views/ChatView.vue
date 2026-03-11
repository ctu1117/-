<template>
  <div class="page">
    <main class="chat-layout">

      <!-- ── 左侧：摄像头 + 实时饼图 ── -->
      <aside class="left-panel glass">

        <!-- 摄像头区域 -->
        <div class="camera-wrapper" id="camera-wrapper">
          <video ref="videoRef" autoplay muted playsinline></video>
          <canvas ref="canvasRef" style="display:none"></canvas>

          <!-- 情绪浮层徽章 -->
          <div class="emotion-overlay">
            <div class="emotion-badge" :class="emotionInfo.cls">
              <span class="emotion-icon">{{ emotionInfo.icon }}</span>
              <div class="emotion-info">
                <span class="emotion-label">{{ emotionInfo.label }}</span>
                <div class="confidence-bar">
                  <div class="confidence-fill" :style="{ width: confidencePct + '%' }"></div>
                </div>
                <span class="confidence-pct">{{ confidencePct }}%</span>
              </div>
            </div>
          </div>

          <!-- 未启动占位 -->
          <div v-if="!cameraStarted" class="camera-placeholder">
            <div class="placeholder-icon">📷</div>
            <p>点击下方按钮启动摄像头</p>
          </div>
        </div>

        <button class="btn btn-primary btn-full" @click="startCamera" :disabled="cameraStarted" id="btn-start">
          {{ cameraStarted ? '✅ 摄像头已启动' : '📷 启动摄像头' }}
        </button>

        <!-- 实时情绪饼图 -->
        <div class="pie-section">
          <h3 class="section-title">本次会话情绪分布</h3>
          <EmotionPieChart :data="sessionEmotionStats" />
          <p v-if="totalEmotions === 0" class="pie-hint">启动摄像头后开始统计...</p>
        </div>
      </aside>

      <!-- ── 右侧：聊天面板 ── -->
      <section class="chat-panel glass">
        <div class="chat-header">
          <div class="ai-avatar">AI</div>
          <div>
            <p class="ai-name">情绪伴侣</p>
            <p class="ai-status">基于 DeepSeek · 实时情绪感知</p>
          </div>
          <div class="emotion-chip" :class="emotionInfo.cls">
            {{ emotionInfo.icon }} {{ emotionInfo.label }}
          </div>
        </div>

        <div class="chat-messages" ref="messagesRef" role="log">
          <div class="message ai-message">
            <div class="bubble">
              👋 你好！我是你的情绪感知 AI 伴侣。<br/>请先启动摄像头，我会感知你的情绪并陪你聊天 ✨
            </div>
          </div>
          <template v-for="msg in messages" :key="msg.id">
            <div class="message" :class="msg.role === 'ai' ? 'ai-message' : 'user-message'">
              <div class="bubble" v-html="msg.html"></div>
            </div>
          </template>
          <!-- 打字动画 -->
          <div v-if="isWaiting" class="message ai-message">
            <div class="bubble typing-bubble">
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
              <div class="typing-dot"></div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <input
            v-model="inputText"
            type="text"
            placeholder="输入消息，和 AI 聊聊吧..."
            @keydown.enter="sendMessage"
            :disabled="isWaiting"
            id="chat-input"
          />
          <button class="btn-send" @click="sendMessage" :disabled="isWaiting" id="btn-send">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { ref, computed, reactive, nextTick, onUnmounted } from 'vue'
import EmotionPieChart from '../components/EmotionPieChart.vue'

// ── 情绪配置 ──────────────────────────────────────────────
const EMOTION_MAP = {
  'Happy :)':   { icon: '😊', cls: 'e-happy',    label: '开心 Happy' },
  'Angry >_<':  { icon: '😠', cls: 'e-angry',    label: '生气 Angry' },
  'Sad  :(':    { icon: '😢', cls: 'e-sad',       label: '伤心 Sad'   },
  'Surprise!':  { icon: '😲', cls: 'e-surprise',  label: '惊讶!'       },
  'Neutral :|': { icon: '😐', cls: 'e-neutral',   label: '平静'        },
  'No Face':    { icon: '🙈', cls: 'e-neutral',   label: '未检测到人脸' },
}

// ── 状态 ──────────────────────────────────────────────────
const videoRef   = ref(null)
const canvasRef  = ref(null)
const messagesRef = ref(null)

const cameraStarted = ref(false)
const currentEmotion = ref('Neutral :|')
const currentConfidence = ref(0.0)
const isWaiting = ref(false)
const inputText = ref('')
const messages  = reactive([])
const chatHistory = reactive([])

// 当前会话 ID
const sessionId = ref(0)
// 本次会话情绪统计
const sessionEmotionStats = reactive({})
const totalEmotions = computed(() => Object.values(sessionEmotionStats).reduce((a, b) => a + b, 0))

let ws = null
let msgCounter = 0

// ── 情绪计算属性 ───────────────────────────────────────────
const emotionInfo = computed(() => EMOTION_MAP[currentEmotion.value] ?? EMOTION_MAP['Neutral :|'])
const confidencePct = computed(() => Math.round(currentConfidence.value * 100))

// ── 启动摄像头 + 创建会话 ─────────────────────────────────
async function startCamera() {
  // 1. 创建数据库会话
  const res = await fetch('/api/session/start', { method: 'POST' })
  const data = await res.json()
  sessionId.value = data.session_id

  // 2. 启动摄像头
  const video  = videoRef.value
  const canvas = canvasRef.value
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
    })
    video.srcObject = stream
    cameraStarted.value = true
    video.addEventListener('loadeddata', () => {
      canvas.width  = video.videoWidth
      canvas.height = video.videoHeight
      connectWebSocket(canvas, video)
    })
  } catch (err) {
    alert('❌ 无法访问摄像头：' + err.message)
  }
}

// ── WebSocket 情绪检测 ────────────────────────────────────
function connectWebSocket(canvas, video) {
  const wsUrl = `ws://${location.host}/ws/emotion/${sessionId.value}`
  ws = new WebSocket(wsUrl)
  const ctx = canvas.getContext('2d')

  ws.onopen = () => {
    setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) return
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      ws.send(canvas.toDataURL('image/jpeg', 0.6))
    }, 200)
  }

  ws.onmessage = (evt) => {
    const { emotion, confidence } = JSON.parse(evt.data)
    currentEmotion.value    = emotion
    currentConfidence.value = confidence
    // 累积饼图统计，排除 No Face
    if (emotion && emotion !== 'No Face') {
      sessionEmotionStats[emotion] = (sessionEmotionStats[emotion] ?? 0) + 1
    }
  }
}

// ── 发送消息 ──────────────────────────────────────────────
async function sendMessage() {
  const msg = inputText.value.trim()
  if (!msg || isWaiting.value) return
  inputText.value = ''

  messages.push({ id: msgCounter++, role: 'user', html: escapeHtml(msg) })
  chatHistory.push({ role: 'user', content: msg })
  scrollToBottom()

  isWaiting.value = true
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message:    msg,
        emotion:    currentEmotion.value,
        confidence: currentConfidence.value,
        history:    chatHistory.slice(-8),
        session_id: sessionId.value,
      }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const { reply } = await res.json()
    messages.push({ id: msgCounter++, role: 'ai', html: escapeHtml(reply) })
    chatHistory.push({ role: 'assistant', content: reply })
  } catch (err) {
    messages.push({ id: msgCounter++, role: 'ai', html: '⚠️ 出错：' + err.message })
  } finally {
    isWaiting.value = false
    scrollToBottom()
  }
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')
}

async function scrollToBottom() {
  await nextTick()
  const el = messagesRef.value
  if (el) el.scrollTop = el.scrollHeight
}

// 页面卸载时结束会话
onUnmounted(() => {
  if (sessionId.value) {
    navigator.sendBeacon(`/api/session/end/${sessionId.value}`, '')
  }
  if (ws) ws.close()
})
</script>

<style scoped>
.chat-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  padding: 16px 20px;
  height: calc(100vh - 72px);
  max-width: 1300px;
  margin: 0 auto;
}

/* ── 左侧面板 ── */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.camera-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #0d0f20;
  border-radius: var(--radius-md);
  overflow: hidden;
}
.camera-wrapper video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-secondary);
}
.placeholder-icon { font-size: 2.5rem; }

/* 情绪浮层 */
.emotion-overlay {
  position: absolute;
  bottom: 10px;
  left: 10px;
  right: 10px;
}
.emotion-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(11,13,26,0.75);
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm);
  backdrop-filter: blur(10px);
  transition: border-color 0.3s;
}
.emotion-icon { font-size: 1.5rem; }
.emotion-info { flex: 1; min-width: 0; }
.emotion-label { font-size: 0.78rem; font-weight: 600; color: var(--text-primary); display: block; }
.confidence-bar { height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin: 4px 0; }
.confidence-fill { height: 100%; border-radius: 2px; background: var(--accent-2); transition: width 0.3s; }
.confidence-pct { font-size: 0.72rem; color: var(--text-secondary); }

.emotion-badge.e-happy  { border-color: rgba(247,201,72,0.4); }
.emotion-badge.e-angry  { border-color: rgba(247,124,106,0.4); }
.emotion-badge.e-sad    { border-color: rgba(110,168,247,0.4); }
.emotion-badge.e-surprise { border-color: rgba(167,139,250,0.4); }

.btn-full { width: 100%; justify-content: center; }

/* 饼图区 */
.pie-section { flex: 1; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.section-title { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }
.pie-hint { font-size: 0.78rem; color: var(--text-secondary); text-align: center; }

/* ── 右侧聊天 ── */
.chat-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-glass);
}
.ai-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.ai-name { font-weight: 600; font-size: 0.9rem; }
.ai-status { font-size: 0.75rem; color: var(--text-secondary); }
.emotion-chip {
  margin-left: auto;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  background: var(--bg-glass-hover);
  border: 1px solid var(--border-glass);
  transition: all 0.3s;
  white-space: nowrap;
}
.emotion-chip.e-happy    { background: rgba(247,201,72,0.15);  border-color: rgba(247,201,72,0.3); }
.emotion-chip.e-angry    { background: rgba(247,124,106,0.15); border-color: rgba(247,124,106,0.3); }
.emotion-chip.e-sad      { background: rgba(110,168,247,0.15); border-color: rgba(110,168,247,0.3); }
.emotion-chip.e-surprise { background: rgba(167,139,250,0.15); border-color: rgba(167,139,250,0.3); }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message { display: flex; }
.user-message { justify-content: flex-end; }
.ai-message   { justify-content: flex-start; }

.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.88rem;
  line-height: 1.6;
  word-break: break-word;
}
.user-message .bubble {
  background: linear-gradient(135deg, var(--accent-1), #5a53c5);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.ai-message .bubble {
  background: var(--bg-glass-hover);
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

/* 打字动画 */
.typing-bubble {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  align-items: center;
}
.typing-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: bounce 1.2s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30%            { transform: translateY(-6px); }
}

/* 输入区 */
.chat-input-area {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-glass);
}
.chat-input-area input {
  flex: 1;
  background: var(--bg-glass-hover);
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  color: var(--text-primary);
  font-size: 0.88rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.chat-input-area input:focus { border-color: var(--accent-1); }
.chat-input-area input::placeholder { color: var(--text-secondary); }

.btn-send {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, var(--accent-1), #5a53c5);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.2s;
}
.btn-send:hover:not(:disabled) { transform: scale(1.08); }
.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-send svg { width: 16px; height: 16px; }
</style>
