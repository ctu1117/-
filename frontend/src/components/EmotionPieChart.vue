<template>
  <div class="pie-wrap">
    <Doughnut :data="chartData" :options="chartOptions" />
    <div v-if="total === 0" class="pie-empty">暂无数据</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { ArcElement, Chart as ChartJS, Legend, Tooltip } from 'chart.js'
import { EMOTION_MAP } from '../utils/emotions'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

const total = computed(() => Object.values(props.data).reduce((sum, value) => sum + value, 0))

const chartData = computed(() => {
  const entries = Object.entries(props.data).filter(([, count]) => count > 0)
  return {
    labels: entries.map(([emotion]) => `${EMOTION_MAP[emotion]?.icon ?? '🙂'} ${EMOTION_MAP[emotion]?.label ?? emotion}`),
    datasets: [
      {
        data: entries.map(([, count]) => count),
        backgroundColor: entries.map(([emotion]) => EMOTION_MAP[emotion]?.color ?? '#94a3b8'),
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 2,
        hoverOffset: 8,
      },
    ],
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
        label: (context) => {
          const sum = context.dataset.data.reduce((acc, item) => acc + item, 0)
          const percentage = sum ? ((context.parsed / sum) * 100).toFixed(1) : 0
          return `${context.label}: ${context.parsed} 次（${percentage}%）`
        },
      },
    },
  },
}
</script>

<style scoped>
.pie-wrap {
  position: relative;
  width: 100%;
  max-width: 280px;
  margin: 0 auto;
}

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
