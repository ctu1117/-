<template>
  <div class="page">
    <div class="journal-page">
      <aside class="journal-sidebar glass">
        <div class="sidebar-top">
          <p class="eyebrow">手记</p>
          <h1>情绪手记</h1>
          <p class="sidebar-copy">把当下的情绪和文字留在这里，像翻看手记一样，安静、轻盈、可回看。</p>
        </div>

        <div class="journal-list">
          <div v-if="loading" class="list-state">正在加载手记...</div>
          <div v-else-if="entries.length === 0" class="list-state">还没有手记，写下第一篇吧。</div>
          <button
            v-for="entry in entries"
            :key="entry.id"
            class="entry-card"
            :class="{ active: selectedEntry?.id === entry.id }"
            @click="selectedEntry = entry"
          >
            <div class="entry-card-top">
              <span class="entry-emoji">{{ getEmotionMeta(entry.emotion).icon }}</span>
              <span class="entry-date">{{ formatDate(entry.created_at) }}</span>
            </div>
            <h3>{{ entry.title || '未命名手记' }}</h3>
            <p>{{ excerpt(entry.content) }}</p>
          </button>
        </div>
      </aside>

      <main class="journal-main">
        <section class="compose-card glass">
          <div class="compose-head">
            <div>
              <p class="eyebrow">新建手记</p>
              <h2>记录这一刻</h2>
            </div>
            <button class="btn btn-primary" @click="saveEntry" :disabled="saving || !canSave">
              {{ saving ? '保存中...' : '保存手记' }}
            </button>
          </div>

          <div class="emotion-picker">
            <button
              v-for="emotion in emotions"
              :key="emotion"
              class="emotion-option"
              :class="[getEmotionMeta(emotion).chipStyle, { selected: selectedEmotion === emotion }]"
              @click="selectedEmotion = emotion"
            >
              <span>{{ getEmotionMeta(emotion).icon }}</span>
              <span>{{ getEmotionMeta(emotion).label }}</span>
            </button>
          </div>

          <input
            v-model="title"
            class="title-input"
            type="text"
            maxlength="120"
            placeholder="给今天起一个标题"
          />

          <textarea
            v-model="content"
            class="note-input"
            maxlength="4000"
            placeholder="今天发生了什么？为什么会有这样的情绪？把它写下来。"
          ></textarea>

          <div class="compose-footer">
            <span>{{ content.length }}/4000</span>
            <span v-if="error" class="error-text">{{ error }}</span>
          </div>
        </section>

        <section class="preview-card glass">
          <div v-if="selectedEntry" class="note-preview">
            <div class="preview-head">
              <div class="preview-emotion" :class="getEmotionMeta(selectedEntry.emotion).chipStyle">
                {{ getEmotionMeta(selectedEntry.emotion).icon }} {{ getEmotionMeta(selectedEntry.emotion).longLabel }}
              </div>
              <button class="btn btn-ghost" @click="removeEntry(selectedEntry.id)">删除</button>
            </div>
            <h2>{{ selectedEntry.title || '未命名手记' }}</h2>
            <p class="preview-date">创建于 {{ formatDateTime(selectedEntry.created_at) }}</p>
            <article class="preview-content">{{ selectedEntry.content }}</article>
          </div>

          <div v-else class="empty-preview">
            <p class="eyebrow">预览</p>
            <h2>选中一篇手记</h2>
            <p>左侧会显示你保存过的手记，这里可以沉浸式阅读和回看。</p>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { apiFetch } from '../utils/api'
import { JOURNAL_EMOTIONS, getEmotionMeta } from '../utils/emotions'

const entries = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const selectedEntry = ref(null)

const emotions = JOURNAL_EMOTIONS
const selectedEmotion = ref('Neutral :|')
const title = ref('')
const content = ref('')

const canSave = computed(() => content.value.trim().length > 0)

onMounted(loadEntries)

async function loadEntries() {
  loading.value = true
  try {
    const res = await apiFetch('/api/journal')
    const data = await res.json()
    entries.value = data
    selectedEntry.value = data[0] ?? null
  } finally {
    loading.value = false
  }
}

async function saveEntry() {
  if (!canSave.value || saving.value) return
  error.value = ''
  saving.value = true
  try {
    const res = await apiFetch('/api/journal', {
      method: 'POST',
      body: JSON.stringify({
        title: title.value,
        content: content.value,
        emotion: selectedEmotion.value,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.detail || '保存失败'
      return
    }
    entries.value = [data, ...entries.value]
    selectedEntry.value = data
    title.value = ''
    content.value = ''
    selectedEmotion.value = 'Neutral :|'
  } catch (err) {
    error.value = '网络异常，请稍后再试'
  } finally {
    saving.value = false
  }
}

async function removeEntry(entryId) {
  if (!confirm('确认删除这篇手记吗？')) return
  const res = await apiFetch(`/api/journal/${entryId}`, { method: 'DELETE' })
  if (!res.ok) return
  entries.value = entries.value.filter((entry) => entry.id !== entryId)
  selectedEntry.value = entries.value[0] ?? null
}

function excerpt(text) {
  return text.length > 56 ? `${text.slice(0, 56)}...` : text
}

function formatDate(iso) {
  const date = new Date(iso)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function formatDateTime(iso) {
  const date = new Date(iso)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day} ${hour}:${minute}`
}
</script>

<style scoped>
.journal-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 18px;
  min-height: calc(100vh - 72px);
}

.journal-sidebar {
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sidebar-top h1,
.compose-head h2,
.preview-card h2 {
  font-family: 'Georgia', 'Times New Roman', serif;
  letter-spacing: 0.02em;
}

.eyebrow {
  color: #9ca3c6;
  font-size: 0.76rem;
  letter-spacing: 0.14em;
  margin-bottom: 8px;
}

.sidebar-copy {
  color: var(--text-secondary);
  line-height: 1.7;
}

.journal-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 4px;
}

.list-state {
  color: var(--text-secondary);
  padding: 24px 8px;
}

.entry-card {
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 248, 238, 0.06);
  border-radius: 20px;
  padding: 16px;
  color: var(--text-primary);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.entry-card:hover,
.entry-card.active {
  transform: translateY(-1px);
  border-color: rgba(255, 255, 255, 0.18);
  background: rgba(255, 248, 238, 0.12);
}

.entry-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.entry-card h3 {
  font-size: 1rem;
  margin-bottom: 6px;
}

.entry-card p,
.entry-date {
  color: var(--text-secondary);
  line-height: 1.6;
}

.journal-main {
  display: grid;
  grid-template-columns: minmax(0, 520px) minmax(0, 1fr);
  gap: 18px;
}

.compose-card,
.preview-card {
  padding: 24px;
}

.compose-card {
  background:
    radial-gradient(circle at top left, rgba(255, 216, 170, 0.22), transparent 35%),
    rgba(255, 250, 244, 0.05);
}

.preview-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)),
    rgba(14, 17, 30, 0.55);
}

.compose-head,
.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.emotion-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.emotion-option {
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  border-radius: 999px;
  padding: 10px 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.emotion-option.selected {
  border-color: rgba(255, 255, 255, 0.24);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.title-input,
.note-input {
  width: 100%;
  border: none;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  border-radius: 18px;
  padding: 16px 18px;
  font-family: inherit;
}

.title-input {
  font-size: 1.05rem;
  margin-bottom: 14px;
}

.note-input {
  min-height: 340px;
  resize: vertical;
  line-height: 1.8;
  font-size: 0.96rem;
}

.title-input:focus,
.note-input:focus {
  outline: 1px solid rgba(255, 255, 255, 0.18);
}

.compose-footer {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 0.78rem;
}

.error-text {
  color: #fda4af;
}

.preview-emotion {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
}

.preview-date {
  color: var(--text-secondary);
  margin: 8px 0 18px;
}

.preview-content {
  white-space: pre-wrap;
  line-height: 1.9;
  color: #edf1ff;
}

.empty-preview {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  justify-content: center;
  color: var(--text-secondary);
}

.emotion-happy { background: rgba(247, 201, 72, 0.14); color: #f7d970; }
.emotion-neutral { background: rgba(125, 211, 199, 0.14); color: #9ae6d7; }
.emotion-sad { background: rgba(110, 168, 247, 0.14); color: #8dbcf9; }
.emotion-angry { background: rgba(247, 124, 106, 0.14); color: #ffb1a4; }
.emotion-surprise { background: rgba(167, 139, 250, 0.14); color: #c4afff; }

@media (max-width: 1100px) {
  .journal-page,
  .journal-main {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .journal-page {
    padding: 14px;
  }

  .compose-head,
  .preview-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
