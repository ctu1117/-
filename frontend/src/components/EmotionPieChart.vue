<template>
  <div class="pie-wrap">
    <Doughnut :data="chartData" :options="chartOptions" />
    <div v-if="total === 0" class="pie-empty">暂无数据</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  // { "Happy :)": 12, "Sad  :(": 3, ... }
  data: { type: Object, default: () => ({}) },
})

const EMOTION_COLORS = {
  'Happy :)':   '#f7c948',
  'Angry >_<':  '#f77c6a',
  'Sad  :(':    '#6ea8f7',
  'Surprise!':  '#a78bfa',
  'Neutral :|': '#5de0e6',
}
const EMOTION_LABELS = {
  'Happy :)':   '😊 开心',
  'Angry >_<':  '😠 生气',
  'Sad  :(':    '😢 伤心',
  'Surprise!':  '😲 惊讶',
  'Neutral :|': '😐 平静',
}

const total = computed(() => Object.values(props.data).reduce((a, b) => a + b, 0))

const chartData = computed(() => {
  const entries = Object.entries(props.data).filter(([, v]) => v > 0)
  return {
    labels: entries.map(([k]) => EMOTION_LABELS[k] ?? k),
    datasets: [{
      data: entries.map(([, v]) => v),
      backgroundColor: entries.map(([k]) => EMOTION_COLORS[k] ?? '#888'),
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 2,
      hoverOffset: 8,
    }],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  cutout: '60%',
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#b0b8d8',
        font: { size: 12, family: 'Noto Sans SC' },
        padding: 14,
        boxWidth: 12,
        boxHeight: 12,
      },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
          const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0
          return `  ${ctx.label}: ${ctx.parsed} 次 (${pct}%)`
        },
      },
    },
  },
}
</script>

<style scoped>
.pie-wrap { position: relative; width: 100%; max-width: 280px; margin: 0 auto; }
.pie-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>
