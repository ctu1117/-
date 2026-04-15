<template>
  <div class="chart-container" ref="chartRef"></div>
</template>

<script setup>
import { markRaw, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { getEmotionMeta } from '../utils/emotions'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let chartInstance = null

function renderChart() {
  if (!chartInstance) return

  const validData = (props.data || []).filter((item) => item.emotion !== 'No Face')
  if (!validData.length) {
    chartInstance.clear()
    chartInstance.setOption({
      title: {
        text: '暂无情绪趋势数据',
        left: 'center',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 14, fontWeight: 500 },
      },
    })
    return
  }

  const xAxisData = validData.map((item) => {
    const date = new Date(item.timestamp)
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
  })

  const seriesData = validData.map((item) => ({
    value: getEmotionMeta(item.emotion).score,
    itemStyle: { color: getEmotionMeta(item.emotion).color },
    emotion: item.emotion,
  }))

  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const point = params[0]
        const meta = getEmotionMeta(point.data.emotion)
        return `${point.axisValue}<br/>${meta.icon} ${meta.label}`
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      min: 1,
      max: 5,
      interval: 1,
      axisLabel: {
        color: '#94a3b8',
        formatter: (value) => ({ 1: '难过', 2: '生气', 3: '平静', 4: '惊讶', 5: '开心' })[value] ?? '',
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
    series: [
      {
        name: '情绪波动',
        type: 'line',
        smooth: true,
        data: seriesData,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(93, 224, 230, 0.25)' },
            { offset: 1, color: 'rgba(93, 224, 230, 0)' },
          ]),
        },
        lineStyle: { width: 3, color: '#5de0e6' },
      },
    ],
  }, true)
}

function handleResize() {
  if (chartInstance) chartInstance.resize()
}

onMounted(() => {
  chartInstance = markRaw(echarts.init(chartRef.value))
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch(() => props.data, renderChart, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) chartInstance.dispose()
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 250px;
}
</style>
