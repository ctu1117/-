<template>
  <div class="page">
    <main class="chat-layout">
      <aside class="left-panel glass">
        <div class="camera-wrapper">
          <video ref="videoRef" autoplay muted playsinline></video>
          <canvas ref="canvasRef" class="hidden-canvas"></canvas>

          <div class="emotion-overlay">
            <div class="emotion-badge" :class="emotionClass">
              <span class="emotion-icon">{{ emotionMeta.icon }}</span>
              <div class="emotion-info">
                <span class="emotion-label">{{ emotionMeta.label }}</span>
                <div class="confidence-bar">
                  <div class="confidence-fill" :style="{ width: `${confidencePct}%` }"></div>
                </div>
                <span class="confidence-pct">{{ confidencePct }}%</span>
              </div>
            </div>
          </div>

          <div v-if="!cameraStarted" class="camera-placeholder">
            <div class="placeholder-icon">📷</div>
            <p>点击下方按钮启动摄像头</p>
          </div>
        </div>

        <button class="btn btn-primary btn-full" @click="startCamera" :disabled="cameraStarted">
          {{ cameraStarted ? '摄像头已启动' : '启动摄像头' }}
        </button>

        <button class="btn btn-ghost btn-full" :disabled="!sessionId" @click="goToJournal">
          为这次会话写手记
        </button>

        <div class="pie-section">
          <h3 class="section-title">本次会话情绪分布</h3>
          <EmotionPieChart :data="sessionEmotionStats" />
          <p v-if="totalEmotions === 0" class="pie-hint">启动摄像头后开始统计情绪。</p>
        </div>
      </aside>

      <section class="chat-panel glass">
        <div class="chat-header">
          <div class="ai-avatar">AI</div>
          <div>
            <p class="ai-name">情绪伴侣</p>
            <p class="ai-status">实时情绪感知 + DeepSeek 陪伴对话</p>
          </div>
          <div class="emotion-chip" :class="emotionClass">
            {{ emotionMeta.icon }} {{ emotionMeta.label }}
          </div>
        </div>

        <div class="chat-messages" ref="messagesRef" role="log">
          <div class="message ai-message">
            <div class="bubble">
              你好，我是你的情绪感知 AI 伴侣。请先启动摄像头，我会感知你的情绪并陪你聊天。
            </div>
          </div>
          <template v-for="message in messages" :key="message.id">
            <div class="message" :class="message.role === 'ai' ? 'ai-message' : 'user-message'">
              <div class="bubble" v-html="message.html"></div>
            </div>
          </template>
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
          />
          <button class="btn-send" @click="sendMessage" :disabled="isWaiting">
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
import { computed, nextTick, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import EmotionPieChart from '../components/EmotionPieChart.vue'
import { apiFetch } from '../utils/api'
import { getEmotionMeta } from '../utils/emotions'

const router = useRouter()
const videoRef = ref(null)
const canvasRef = ref(null)
const messagesRef = ref(null)

const cameraStarted = ref(false)
const currentEmotion = ref('Neutral :|')
const currentConfidence = ref(0)
const isWaiting = ref(false)
const inputText = ref('')
const messages = reactive([])
const chatHistory = reactive([])
const sessionEmotionStats = reactive({})
const sessionId = ref(0)

let ws = null
let captureTimer = null
let messageCounter = 0

const emotionMeta = computed(() => getEmotionMeta(currentEmotion.value))
const confidencePct = computed(() => Math.round(currentConfidence.value * 100))
const totalEmotions = computed(() => Object.values(sessionEmotionStats).reduce((sum, value) => sum + value, 0))
const emotionClass = computed(() => ({
  'emotion-happy': currentEmotion.value === 'Happy :)',
  'emotion-angry': currentEmotion.value === 'Angry >_<',
  'emotion-sad': currentEmotion.value === 'Sad  :(',
  'emotion-surprise': currentEmotion.value === 'Surprise!',
  'emotion-neutral': currentEmotion.value === 'Neutral :|' || currentEmotion.value === 'No Face',
}))

async function startCamera() {
  const sessionResponse = await apiFetch('/api/session/start', { method: 'POST' })
  const sessionData = await sessionResponse.json()
  sessionId.value = sessionData.session_id

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
    })
    const video = videoRef.value
    const canvas = canvasRef.value
    video.srcObject = stream
    cameraStarted.value = true

    video.addEventListener('loadeddata', () => {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      connectWebSocket(canvas, video)
    }, { once: true })
  } catch (error) {
    alert(`无法访问摄像头：${error.message}`)
  }
}

function connectWebSocket(canvas, video) {
  ws = new WebSocket(`ws://${location.host}/ws/emotion/${sessionId.value}`)
  const context = canvas.getContext('2d')

  ws.onopen = () => {
    captureTimer = window.setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) return
      context.drawImage(video, 0, 0, canvas.width, canvas.height)
      ws.send(canvas.toDataURL('image/jpeg', 0.6))
    }, 200)
  }

  ws.onmessage = (event) => {
    const { emotion, confidence } = JSON.parse(event.data)
    currentEmotion.value = emotion
    currentConfidence.value = confidence
    if (emotion && emotion !== 'No Face') {
      sessionEmotionStats[emotion] = (sessionEmotionStats[emotion] ?? 0) + 1
    }
  }
}

async function sendMessage() {
  const message = inputText.value.trim()
  if (!message || isWaiting.value) return

  inputText.value = ''
  messages.push({ id: messageCounter++, role: 'user', html: escapeHtml(message) })
  chatHistory.push({ role: 'user', content: message })
  await scrollToBottom()

  isWaiting.value = true
  try {
    const response = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        emotion: currentEmotion.value,
        confidence: currentConfidence.value,
        history: chatHistory.slice(-8),
        session_id: sessionId.value,
      }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    messages.push({ id: messageCounter++, role: 'ai', html: escapeHtml(data.reply) })
    chatHistory.push({ role: 'assistant', content: data.reply })
  } catch (error) {
    messages.push({ id: messageCounter++, role: 'ai', html: `出错了：${escapeHtml(error.message)}` })
  } finally {
    isWaiting.value = false
    await scrollToBottom()
  }
}

function goToJournal() {
  if (!sessionId.value) return
  router.push({
    path: '/journal',
    query: {
      session_id: String(sessionId.value),
      emotion: currentEmotion.value,
    },
  })
}

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

onUnmounted(() => {
  if (captureTimer) {
    clearInterval(captureTimer)
  }
  if (sessionId.value) {
    navigator.sendBeacon(`/api/session/end/${sessionId.value}`, '')
  }
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.chat-layout { display: grid; grid-template-columns: 360px 1fr; gap: 16px; padding: 16px 20px; min-height: calc(100vh - 72px); max-width: 1300px; margin: 0 auto; }
.left-panel { display: flex; flex-direction: column; gap: 16px; padding: 16px; overflow: hidden; }
.camera-wrapper { position: relative; width: 100%; aspect-ratio: 4/3; background: #0d0f20; border-radius: var(--radius-md); overflow: hidden; }
.camera-wrapper video { width: 100%; height: 100%; object-fit: cover; display: block; }
.hidden-canvas { display: none; }
.camera-placeholder { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: var(--text-secondary); }
.placeholder-icon { font-size: 2.5rem; }
.emotion-overlay { position: absolute; bottom: 10px; left: 10px; right: 10px; }
.emotion-badge { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: rgba(11,13,26,0.75); border: 1px solid var(--border-glass); border-radius: var(--radius-sm); backdrop-filter: blur(10px); }
.emotion-icon { font-size: 1.5rem; }
.emotion-info { flex: 1; min-width: 0; }
.emotion-label { font-size: 0.78rem; font-weight: 600; color: var(--text-primary); display: block; }
.confidence-bar { height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin: 4px 0; }
.confidence-fill { height: 100%; border-radius: 2px; background: var(--accent-2); transition: width 0.3s; }
.confidence-pct { font-size: 0.72rem; color: var(--text-secondary); }
.emotion-badge.emotion-happy { border-color: rgba(247,201,72,0.4); }
.emotion-badge.emotion-angry { border-color: rgba(247,124,106,0.4); }
.emotion-badge.emotion-sad { border-color: rgba(110,168,247,0.4); }
.emotion-badge.emotion-surprise { border-color: rgba(167,139,250,0.4); }
.btn-full { width: 100%; justify-content: center; }
.pie-section { flex: 1; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.section-title { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }
.pie-hint { font-size: 0.78rem; color: var(--text-secondary); text-align: center; }
.chat-panel { display: flex; flex-direction: column; overflow: hidden; }
.chat-header { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--border-glass); }
.ai-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; color: #fff; }
.ai-name { font-weight: 600; font-size: 0.9rem; }
.ai-status { font-size: 0.75rem; color: var(--text-secondary); }
.emotion-chip { margin-left: auto; padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; background: var(--bg-glass-hover); border: 1px solid var(--border-glass); white-space: nowrap; }
.emotion-chip.emotion-happy { background: rgba(247,201,72,0.15); border-color: rgba(247,201,72,0.3); }
.emotion-chip.emotion-angry { background: rgba(247,124,106,0.15); border-color: rgba(247,124,106,0.3); }
.emotion-chip.emotion-sad { background: rgba(110,168,247,0.15); border-color: rgba(110,168,247,0.3); }
.emotion-chip.emotion-surprise { background: rgba(167,139,250,0.15); border-color: rgba(167,139,250,0.3); }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px 18px; display: flex; flex-direction: column; gap: 12px; }
.message { display: flex; }
.user-message { justify-content: flex-end; }
.ai-message { justify-content: flex-start; }
.bubble { max-width: 72%; padding: 10px 14px; border-radius: var(--radius-md); font-size: 0.88rem; line-height: 1.6; word-break: break-word; }
.user-message .bubble { background: linear-gradient(135deg, var(--accent-1), #5a53c5); color: #fff; border-bottom-right-radius: 4px; }
.ai-message .bubble { background: var(--bg-glass-hover); border: 1px solid var(--border-glass); color: var(--text-primary); border-bottom-left-radius: 4px; }
.typing-bubble { display: flex; gap: 5px; padding: 14px 18px; align-items: center; }
.typing-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--text-secondary); animation: bounce 1.2s ease-in-out infinite; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
.chat-input-area { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-top: 1px solid var(--border-glass); }
.chat-input-area input { flex: 1; background: var(--bg-glass-hover); border: 1px solid var(--border-glass); border-radius: var(--radius-sm); padding: 10px 14px; color: var(--text-primary); font-size: 0.88rem; font-family: inherit; outline: none; }
.chat-input-area input:focus { border-color: var(--accent-1); }
.chat-input-area input::placeholder { color: var(--text-secondary); }
.btn-send { width: 40px; height: 40px; border-radius: 50%; border: none; cursor: pointer; background: linear-gradient(135deg, var(--accent-1), #5a53c5); color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: transform 0.2s; }
.btn-send:hover:not(:disabled) { transform: scale(1.08); }
.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-send svg { width: 16px; height: 16px; }
@media (max-width: 1100px) { .chat-layout { grid-template-columns: 1fr; } }
</style>
