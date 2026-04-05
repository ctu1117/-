<template>
  <div class="calendar-container" ref="chartRef"></div>
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
  'Sad  :(': 1
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
    
    if (!props.data || props.data.length === 0) {
        chartInstance.clear();
        return;
    }

    const seriesData = props.data.map(item => {
        return [
            item[0],
            EMOTION_SCORE[item[1]] || 3,
            item[1]
        ];
    });
    
    // 计算时间范围：以当前月份为终点，向前推 2 个月
    const today = new Date();
    const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0); // 本月末
    const startDate = new Date(today.getFullYear(), today.getMonth() - 2, 1); // 前推2个月初
    
    const fmt = (d) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    const rangeStr = [fmt(startDate), fmt(endDate)];

    const option = {
        tooltip: {
            formatter: function (p) {
                if (!p.data || !Array.isArray(p.data)) return '';
                const emotionText = SCORE_LABEL[p.data[1]] || p.data[2];
                return `${p.data[0]}<br>主导情绪: ${emotionText}`;
            }
        },
        visualMap: {
            min: 1,
            max: 5,
            type: 'piecewise',
            orient: 'horizontal',
            left: 'center',
            top: 0,
            itemGap: 12,
            textStyle: { color: '#94a3b8', fontSize: 12 },
            pieces: [
                {value: 1, label: '伤心', color: EMOTION_COLORS['Sad  :(']},
                {value: 2, label: '生气', color: EMOTION_COLORS['Angry >_<']},
                {value: 3, label: '平静', color: EMOTION_COLORS['Neutral :|']},
                {value: 4, label: '惊讶', color: EMOTION_COLORS['Surprise!']},
                {value: 5, label: '开心', color: EMOTION_COLORS['Happy :)']}
            ]
        },
        calendar: {
            top: 50,
            left: 40,
            right: 15,
            bottom: 10,
            cellSize: [18, 18],
            range: rangeStr,
            splitLine: {
                show: false
            },
            itemStyle: {
                borderWidth: 3,
                borderColor: 'rgba(30, 41, 59, 0.9)',
                borderRadius: 3,
                color: 'rgba(255,255,255,0.04)'
            },
            yearLabel: { show: false },
            dayLabel: {
                firstDay: 1,
                nameMap: ['日', '一', '二', '三', '四', '五', '六'],
                color: '#64748b',
                fontSize: 11
            },
            monthLabel: {
                nameMap: 'ZH',
                color: '#94a3b8',
                fontSize: 12
            }
        },
        series: {
            type: 'heatmap',
            coordinateSystem: 'calendar',
            data: seriesData,
            itemStyle: {
                borderRadius: 3
            }
        }
    };
    
    chartInstance.setOption(option, true); // true = 清除旧配置
};

const handleResize = () => {
    if (chartInstance) chartInstance.resize();
};

onMounted(() => {
    chartInstance = markRaw(echarts.init(chartRef.value));
    renderChart();
    window.addEventListener('resize', handleResize);
});

watch(() => props.data, () => {
    renderChart();
}, { deep: true });

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (chartInstance) {
        chartInstance.dispose();
    }
});
</script>

<style scoped>
.calendar-container {
    width: 100%;
    height: 240px;
}
</style>
