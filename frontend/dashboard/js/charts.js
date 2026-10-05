/**
 * Charts Module - Felix Dashboard
 * Handles Chart.js visualizations
 * FASE 12 Frontend
 */

let pipelineChart = null;

/**
 * Initialize all charts
 */
async function initializeCharts() {
    try {
        const kpis = await getDashboardKPIs();

        // Update KPI cards
        updateKPICards(kpis);

        // Create pipeline chart
        createPipelineChart(kpis.pipeline);

    } catch (error) {
        console.error('❌ Chart initialization error:', error);
    }
}

/**
 * Update KPI cards with data
 */
function updateKPICards(kpis) {
    // Total clients
    const totalElement = document.getElementById('totalClientes');
    if (totalElement) {
        totalElement.textContent = formatNumber(kpis.total_clientes);
    }

    // Active clients
    const activosElement = document.getElementById('activosClientes');
    if (activosElement) {
        activosElement.textContent = formatNumber(kpis.clientes_activos);
    }

    // Conversion rate
    const conversionElement = document.getElementById('conversionRate');
    if (conversionElement) {
        conversionElement.textContent = `${kpis.conversion_rate.toFixed(1)}%`;
    }

    // Revenue forecast
    const revenueElement = document.getElementById('revenue');
    if (revenueElement) {
        revenueElement.textContent = formatCurrency(kpis.revenue_forecast_monthly);
    }

    // Average score
    const scoreElement = document.getElementById('avgScore');
    if (scoreElement) {
        scoreElement.textContent = kpis.score_promedio.toFixed(0);
    }
}

/**
 * Create pipeline chart
 */
function createPipelineChart(pipelineData) {
    const canvas = document.getElementById('pipelineChart');
    if (!canvas) return;

    // Destroy existing chart if any
    if (pipelineChart) {
        pipelineChart.destroy();
    }

    const stages = ['prospecto', 'propuesta', 'negociacion', 'cerrado'];
    const values = stages.map(stage => pipelineData[stage] || 0);
    const colors = [
        '#3B82F6',  // Prospecto - Blue
        '#F59E0B',  // Propuesta - Amber
        '#8B5CF6',  // Negociación - Purple
        '#10B981'   // Cerrado - Green
    ];

    pipelineChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: [
                '📋 Prospecto',
                '📄 Propuesta',
                '💬 Negociación',
                '✅ Cerrado'
            ],
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#FFFFFF',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            family: "system-ui, -apple-system, sans-serif",
                            size: 13,
                            weight: '500'
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return ` ${value} clientes (${percentage}%)`;
                        }
                    },
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    displayColors: true,
                    borderColor: '#ccc',
                    borderWidth: 1
                }
            }
        }
    });
}

/**
 * Create conversion rate chart
 */
function createConversionChart(data) {
    const canvas = document.getElementById('conversionChart');
    if (!canvas) return;

    const chart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: ['Prospecto', 'Propuesta', 'Negociación', 'Cerrado'],
            datasets: [{
                label: 'Clientes',
                data: [
                    data.prospecto || 0,
                    data.propuesta || 0,
                    data.negociacion || 0,
                    data.cerrado || 0
                ],
                backgroundColor: [
                    '#3B82F6',
                    '#F59E0B',
                    '#8B5CF6',
                    '#10B981'
                ],
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'x',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    return chart;
}

/**
 * Create line chart for trends
 */
function createTrendChart(canvasId, labels, datasets) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    return new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Update charts on data refresh
 */
async function refreshCharts() {
    showLoading(true);
    try {
        await initializeCharts();
    } finally {
        showLoading(false);
    }
}

/**
 * Export chart as image
 */
function exportChartAsImage(chartId, fileName) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;

    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = `${fileName}.png`;
    link.click();
}

/**
 * Create mini KPI badge with trend
 */
function createKPIBadge(label, value, trend = null) {
    const badge = document.createElement('div');
    badge.className = 'kpi-badge';

    let trendHTML = '';
    if (trend) {
        const trendClass = trend > 0 ? 'trend-up' : 'trend-down';
        const trendIcon = trend > 0 ? '📈' : '📉';
        trendHTML = `<span class="${trendClass}">${trendIcon} ${Math.abs(trend).toFixed(1)}%</span>`;
    }

    badge.innerHTML = `
        <div class="badge-label">${label}</div>
        <div class="badge-value">${value}</div>
        ${trendHTML}
    `;

    return badge;
}

/**
 * Create status indicator
 */
function createStatusIndicator(status) {
    const indicator = document.createElement('div');
    indicator.className = `status-indicator ${status}`;
    return indicator;
}

/**
 * Animate number count up
 */
function animateNumberCount(element, target, duration = 1000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const animate = () => {
        current += increment;
        if (current < target) {
            element.textContent = Math.floor(current).toLocaleString();
            requestAnimationFrame(animate);
        } else {
            element.textContent = Math.floor(target).toLocaleString();
        }
    };

    animate();
}

/**
 * Create comparison chart
 */
function createComparisonChart(canvasId, label1, value1, label2, value2) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    return new Chart(canvas, {
        type: 'bar',
        data: {
            labels: [label1, label2],
            datasets: [{
                label: 'Comparación',
                data: [value1, value2],
                backgroundColor: ['#4F46E5', '#EC4899'],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { beginAtZero: true }
            }
        }
    });
}

// Auto-refresh charts every 5 minutes
setInterval(() => {
    console.log('🔄 Refreshing charts...');
    refreshCharts();
}, 5 * 60 * 1000);

// Export functions for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeCharts,
        refreshCharts,
        updateKPICards,
        createPipelineChart
    };
}
