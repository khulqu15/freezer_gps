<template>
    <div class="">
        <button class="btn btn-primary" @click="resetZoom">Reset Zoom</button>
        <div class="h-full w-full min-h-[50vh]">
            <Line ref="chartRef" :data="chartData" :options="chartOptions" />
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, computed, PropType, nextTick, watch, ref } from "vue";
import {
    Chart as Chartjs,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    ChartOptions,
    ChartData,
    Legend,
    Filler
} from 'chart.js';
import { Line } from 'vue-chartjs';
import zoomPlugin from 'chartjs-plugin-zoom';

Chartjs.register(LineElement, PointElement, LinearScale, Title, CategoryScale, Tooltip, Legend, Filler, zoomPlugin);

export default defineComponent({
    name: "WaveChart",
    components: {
        Line,
    },
    props: {
        waveData: {
            type: Array as PropType<Array<Array<{ value: number; date: string }>>>,
            required: true,
        },
        waveNames: {
            type: Array as PropType<Array<string>>,
            required: true,
        }
    },

    setup(props) {
        const colors = ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)', 'rgba(153, 102, 255, 1)'];
        const chartRef = ref<any>(null);
        let lastZoomState: any = null;
        const formatDate = (dateString: string) => {
            const date = new Date(dateString);
            const options: Intl.DateTimeFormatOptions = { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
            return date.toLocaleString('en-US', options);
        };
        
        const chartData = computed<ChartData<'line'>>(() => {
            const maxPoints = 50;

            const labels = props.waveData[0]
                ?.slice(-maxPoints)
                .map(data => formatDate(data.date)) || [];

            const datasets = props.waveData.map((data, index) => {
                const recentData = data.slice(-maxPoints);
                return {
                    label: props.waveNames[index],
                    data: recentData.map(d => d.value),
                    borderColor: colors[index % colors.length],
                    backgroundColor: colors[index % colors.length].replace('1)', '0.2)'),
                    fill: true,
                };
            });

            return {
                labels,
                datasets,
            };
        });

        const getYLimits = () => {
            let allValues: number[] = [];
            props.waveData.forEach(series => {
                series.forEach(point => {
                    allValues.push(point.value);
                });
            });

            if (allValues.length === 0) return { min: 0, max: 10 };

            const minVal = Math.min(...allValues);
            const maxVal = Math.max(...allValues);

            return {
                min: minVal >= 0 ? 0 : Math.floor(minVal - 1),
                max: Math.ceil(maxVal + 1)
            };
        };

        watch(chartData, async () => {
            if (chartRef.value?.chart && lastZoomState?.x) {
                await nextTick(); // tunggu chart re-render
                const chart = chartRef.value.chart;

                chart.options.scales!.x!.min = lastZoomState.x.min;
                chart.options.scales!.x!.max = lastZoomState.x.max;

                if (lastZoomState.y) {
                    chart.options.scales!.y!.min = lastZoomState.y.min;
                    chart.options.scales!.y!.max = lastZoomState.y.max;
                }

                chart.update('none');
            }
        });


        const chartOptions = computed<ChartOptions<'line'>>(() => {
            const { min, max } = getYLimits();

            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: {
                        display: true,
                        text: 'Diagram',
                    },
                    tooltip: { enabled: true },
                    zoom: {
                        pan: { enabled: true, mode: 'x' },
                        zoom: {
                            wheel: { enabled: true },
                            pinch: { enabled: true },
                            mode: 'x',
                            onZoom: ({ chart }) => {
                                lastZoomState = {
                                    x: chart.scales.x.min !== undefined && chart.scales.x.max !== undefined
                                    ? { min: chart.scales.x.min, max: chart.scales.x.max }
                                    : null,
                                    y: chart.scales.y.min !== undefined && chart.scales.y.max !== undefined
                                    ? { min: chart.scales.y.min, max: chart.scales.y.max }
                                    : null,
                                };
                            }
                        },
                    },
                },
                scales: {
                    x: {
                        type: 'category',
                        title: { display: true, text: 'Time' },
                        ticks: { autoSkip: true, maxTicksLimit: 10 },
                    },
                    y: {
                        type: 'linear',
                        title: { display: true, text: 'Value' },
                        min,
                        max,
                    },
                },
            };
        });

        const resetZoom = () => {
            if (chartRef.value?.chart) {
                chartRef.value.chart.resetZoom();
                lastZoomState = null;
            }
        };

        return {
            chartData,
            resetZoom,
            chartOptions,
            chartRef,
        };
    },
});
</script>
