<template>
  <div class="chart-container" ref="chartRef"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, markRaw } from 'vue';
import * as echarts from 'echarts';

const props = defineProps(['data']);
const chartRef = ref(null);
let chartInstance = null;

const EMOTION_COLORS = {
  'Happy :)': '#f7c948',
  'Angry >_<': '#f77c6a',
  'Sad  :(': '#6ea8f7',
  'Surprise!': '#a78bfa',
  'Neutral :|': '#9ca3af'
};

const EMOTION_SCORE = {
  'Happy :)': 5,
  'Surprise!': 4,
  'Neutral :|': 3,
  'Angry >_<': 2,
  'Sad  :(': 1,
  'No Face': null
};

const SCORE_LABEL = {
  5: '开心',
  4: '惊讶',
  3: '平静',
  2: '生气',
  1: '伤心'
};

const renderChart = () => {
    if (!chartInstance) return;
    
    // Process data
    const validData = (props.data || []).filter(item => item.emotion !== 'No Face');
    if (validData.length === 0) {
        chartInstance.clear();
        return;
    }

    const times = validData.map(item => {
        const d = new Date(item.timestamp);
        return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
    });
    
    const scores = validData.map(item => ({
        value: EMOTION_SCORE[item.emotion],
        itemStyle: { color: EMOTION_COLORS[item.emotion] }
    }));

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                const pt = params[0];
                const score = pt.data.value;
                return `${pt.axisValue}<br/><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${pt.data.itemStyle.color};"></span>情绪: ${SCORE_LABEL[score]}`;
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '10%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: times,
            axisLine: { lineStyle: { color: 'rgba(0,0,0,0.15)' } },
            axisLabel: { color: '#78716c' }
        },
        yAxis: {
            type: 'value',
            min: 1,
            max: 5,
            interval: 1,
            axisLabel: {
                color: '#78716c',
                formatter: function (value) { return SCORE_LABEL[value] || ''; }
            },
            splitLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } }
        },
        series: [
            {
                name: '情绪波动',
                type: 'line',
                smooth: true,
                data: scores,
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: 'rgba(202, 138, 4, 0.3)' },
                      { offset: 1, color: 'rgba(202, 138, 4, 0)' }
                    ])
                },
                lineStyle: {
                    width: 3,
                    color: '#ca8a04'
                }
            }
        ]
    };
    chartInstance.setOption(option);
};

onMounted(() => {
    chartInstance = markRaw(echarts.init(chartRef.value));
    renderChart();
    window.addEventListener('resize', () => chartInstance.resize());
});

watch(() => props.data, () => {
    renderChart();
}, { deep: true });

onUnmounted(() => {
    if (chartInstance) {
        chartInstance.dispose();
    }
});
</script>

<style scoped>
.chart-container {
    width: 100%;
    height: 100%;
    min-height: 250px;
}
</style>
