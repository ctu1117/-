<template>
  <div class="page">
    <div class="detail-page">
      <section v-if="loading" class="glass state-card">
        <p>正在加载手记详情...</p>
      </section>

      <section v-else-if="!entry" class="glass state-card">
        <h1>未找到手记</h1>
        <p>这篇手记可能已被删除，或者不属于当前登录用户。</p>
        <RouterLink class="btn btn-primary" to="/journal">返回手记页</RouterLink>
      </section>

      <template v-else>
        <section class="hero-card glass">
          <div>
            <p class="eyebrow">Journal Detail</p>
            <h1>{{ entry.title || '未命名手记' }}</h1>
          </div>
          <div class="hero-side">
            <div class="hero-emotion" :class="getEmotionMeta(entry.emotion).chipStyle">
              <span>{{ getEmotionMeta(entry.emotion).icon }}</span>
              <span>{{ getEmotionMeta(entry.emotion).label }}</span>
            </div>
            <div class="hero-time">记录于 {{ formatDateTime(entry.created_at) }}</div>
          </div>
        </section>

        <section class="content-grid">
          <article class="content-card glass">
            <div class="section-head">
              <h2>手记正文</h2>
              <RouterLink class="section-link" to="/journal">返回手记页</RouterLink>
            </div>
            <p class="content-body">{{ entry.content }}</p>
          </article>

          <aside class="info-card glass">
            <div class="section-head">
              <h2>记录信息</h2>
            </div>
            <div class="info-list">
              <div class="info-item">
                <span class="info-label">主观情绪</span>
                <span class="info-value">{{ getEmotionMeta(entry.emotion).icon }} {{ getEmotionMeta(entry.emotion).longLabel }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">创建时间</span>
                <span class="info-value">{{ formatDateTime(entry.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">更新时间</span>
                <span class="info-value">{{ formatDateTime(entry.updated_at) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">关联会话</span>
                <span v-if="entry.session_id" class="info-value">
                  <RouterLink class="section-link" :to="`/session/${entry.session_id}`">查看会话 #{{ entry.session_id }}</RouterLink>
                </span>
                <span v-else class="info-value">未绑定会话</span>
              </div>
            </div>
          </aside>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { apiFetch } from '../utils/api'
import { getEmotionMeta } from '../utils/emotions'

const route = useRoute()
const loading = ref(true)
const entry = ref(null)

onMounted(loadEntry)
watch(() => route.params.id, loadEntry)

async function loadEntry() {
  loading.value = true
  try {
    const entryId = Number(route.params.id)
    const response = await apiFetch('/api/journal')
    const data = await response.json()
    entry.value = data.find((item) => item.id === entryId) ?? null
  } finally {
    loading.value = false
  }
}

function formatDateTime(iso) {
  if (!iso) return '-'
  const date = new Date(iso)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.detail-page { max-width: 1240px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.state-card { padding: 32px; text-align: center; display: flex; flex-direction: column; gap: 12px; align-items: center; }
.hero-card { display: flex; justify-content: space-between; gap: 18px; padding: 26px; }
.eyebrow { color: #9ca3c6; font-size: 0.76rem; letter-spacing: 0.14em; margin-bottom: 8px; }
.hero-copy { max-width: 720px; color: var(--text-secondary); line-height: 1.8; margin-top: 12px; }
.hero-side { display: flex; flex-direction: column; align-items: flex-end; gap: 12px; }
.hero-emotion { display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 999px; }
.hero-time { color: var(--text-secondary); font-size: 0.84rem; }
.content-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.8fr); gap: 14px; }
.content-card, .info-card { padding: 20px; }
.section-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-head h2 { font-size: 1rem; }
.section-link { color: var(--accent-1); text-decoration: none; font-size: 0.84rem; }
.content-body { white-space: pre-wrap; line-height: 1.9; color: #edf1ff; }
.info-list { display: flex; flex-direction: column; gap: 14px; }
.info-item { padding: 14px; border-radius: 16px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); display: flex; flex-direction: column; gap: 6px; }
.info-label { color: var(--text-secondary); font-size: 0.78rem; }
.info-value { font-size: 0.96rem; }
.emotion-happy { background: rgba(247,201,72,0.14); color: #f7d970; }
.emotion-neutral { background: rgba(125,211,199,0.14); color: #9ae6d7; }
.emotion-sad { background: rgba(110,168,247,0.14); color: #8dbcf9; }
.emotion-angry { background: rgba(247,124,106,0.14); color: #ffb1a4; }
.emotion-surprise { background: rgba(167,139,250,0.14); color: #c4afff; }
@media (max-width: 980px) {
  .hero-card,
  .content-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
  .hero-side {
    align-items: flex-start;
  }
}
</style>
