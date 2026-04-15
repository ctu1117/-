<template>
  <div class="page">
    <div class="guide-page">
      <section class="hero-card glass">
        <div>
          <p class="eyebrow">Emotion Guide</p>
          <h1>情绪识别说明页</h1>
          <p class="hero-copy">
            该页面用于介绍系统如何完成实时情绪识别、为什么需要稳定化处理，以及在实际使用中需要注意的环境条件。
          </p>
        </div>
        <div class="hero-badge glass-subtle">
          <div class="badge-title">核心链路</div>
          <div class="badge-value">摄像头采集 → 特征提取 → 情绪判定 → 稳定化输出</div>
        </div>
      </section>

      <section class="grid-two">
        <article class="panel-card glass">
          <h2>识别原理</h2>
          <p>
            系统通过摄像头采集用户人脸图像，利用 MediaPipe Face Landmarker 提取面部关键点和表情特征参数，
            再依据不同情绪对应的典型面部动作设计规则评分方法，从而识别开心、生气、难过、惊讶和平静等状态。
          </p>
        </article>

        <article class="panel-card glass">
          <h2>稳定化策略</h2>
          <p>
            为避免单帧识别带来的抖动，系统对最近若干帧结果进行投票和置信度约束处理，只有达到稳定条件的情绪才会用于界面显示和日志存储，
            这样可以提升折线图、历史分析和今日报告的数据可靠性。
          </p>
        </article>
      </section>

      <section class="grid-two">
        <article class="panel-card glass">
          <h2>支持的情绪类别</h2>
          <div class="emotion-list">
            <div v-for="emotion in emotions" :key="emotion.key" class="emotion-item" :class="emotion.meta.chipStyle">
              <span class="emotion-icon">{{ emotion.meta.icon }}</span>
              <div>
                <div class="emotion-name">{{ emotion.meta.label }}</div>
                <div class="emotion-desc">{{ emotion.desc }}</div>
              </div>
            </div>
          </div>
        </article>

        <article class="panel-card glass">
          <h2>使用注意事项</h2>
          <ul class="tips-list">
            <li>尽量保持正面朝向摄像头，避免大幅度侧脸。</li>
            <li>光线过暗或过强都会影响关键点识别效果。</li>
            <li>口罩、头发遮挡、快速晃动都可能造成误判。</li>
            <li>建议在情绪变化较明显时进行体验，展示效果更直观。</li>
          </ul>
        </article>
      </section>

      <section class="panel-card glass">
        <h2>系统闭环说明</h2>
        <div class="flow-grid">
          <div class="flow-item">
            <span class="flow-step">1</span>
            <h3>实时感知</h3>
            <p>在对话页启动摄像头，实时识别当前情绪。</p>
          </div>
          <div class="flow-item">
            <span class="flow-step">2</span>
            <h3>过程记录</h3>
            <p>把情绪结果与会话消息一起存入历史记录。</p>
          </div>
          <div class="flow-item">
            <span class="flow-step">3</span>
            <h3>结果分析</h3>
            <p>在历史分析页和今日报告页展示图表与统计结果。</p>
          </div>
          <div class="flow-item">
            <span class="flow-step">4</span>
            <h3>主观补充</h3>
            <p>通过情绪手记记录主观感受，形成完整闭环。</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { EMOTION_MAP } from '../utils/emotions'

const descriptions = {
  'Happy :)': '嘴角上扬、面部放松，通常表示积极愉悦。',
  'Angry >_<': '眉部收紧、眼部紧张，通常表示愤怒或烦躁。',
  'Sad  :(': '嘴角下压、神情低落，通常表示难过或沮丧。',
  'Surprise!': '眼睛睁大、嘴部张开，通常表示惊讶或意外。',
  'Neutral :|': '表情相对平稳，表示当前情绪较为平静。',
}

const emotions = computed(() =>
  ['Happy :)', 'Neutral :|', 'Sad  :(', 'Angry >_<', 'Surprise!'].map((key) => ({
    key,
    meta: EMOTION_MAP[key],
    desc: descriptions[key],
  })),
)
</script>

<style scoped>
.guide-page { max-width: 1280px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 18px; }
.hero-card { display: flex; justify-content: space-between; align-items: center; gap: 18px; padding: 28px; }
.eyebrow { color: #9ca3c6; font-size: 0.76rem; letter-spacing: 0.14em; margin-bottom: 8px; }
.hero-copy { max-width: 760px; color: var(--text-secondary); line-height: 1.8; margin-top: 10px; }
.glass-subtle { padding: 18px; border-radius: 22px; background: rgba(255,255,255,0.05); border: 1px solid var(--border-glass); min-width: 280px; }
.badge-title { color: var(--text-secondary); font-size: 0.82rem; margin-bottom: 6px; }
.badge-value { font-size: 1rem; font-weight: 600; line-height: 1.6; }
.grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.panel-card { padding: 20px; }
.panel-card h2 { font-size: 1rem; margin-bottom: 12px; }
.panel-card p { color: var(--text-secondary); line-height: 1.8; }
.emotion-list { display: flex; flex-direction: column; gap: 10px; }
.emotion-item { display: flex; gap: 12px; align-items: flex-start; padding: 14px; border-radius: 16px; }
.emotion-icon { font-size: 1.25rem; }
.emotion-name { font-weight: 600; margin-bottom: 4px; }
.emotion-desc { font-size: 0.84rem; line-height: 1.7; }
.tips-list { margin: 0; padding-left: 18px; color: var(--text-secondary); line-height: 1.9; }
.flow-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.flow-item { padding: 16px; border-radius: 16px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); }
.flow-step { display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: rgba(124,106,247,0.2); color: var(--accent-1); font-weight: 700; margin-bottom: 10px; }
.flow-item h3 { font-size: 0.95rem; margin-bottom: 8px; }
.flow-item p { font-size: 0.84rem; color: var(--text-secondary); line-height: 1.7; }
.emotion-happy { background: rgba(247,201,72,0.14); color: #f7d970; }
.emotion-neutral { background: rgba(125,211,199,0.14); color: #9ae6d7; }
.emotion-sad { background: rgba(110,168,247,0.14); color: #8dbcf9; }
.emotion-angry { background: rgba(247,124,106,0.14); color: #ffb1a4; }
.emotion-surprise { background: rgba(167,139,250,0.14); color: #c4afff; }
@media (max-width: 1100px) {
  .hero-card,
  .grid-two,
  .flow-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
