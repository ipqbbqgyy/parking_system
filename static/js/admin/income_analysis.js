const incomeConfig = {
    currentPeriod: 'today',
    incomeTrendChart: null
};

// 格式化金额显示
function formatMoney(amount) {
    return parseFloat(amount || 0).toFixed(2);
}

document.addEventListener('DOMContentLoaded', function() {
    // 初始化统计卡片动画
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, index * 150);
    });

    // 时间标签切换
    document.querySelectorAll('.time-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.time-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            incomeConfig.currentPeriod = this.dataset.period;
            fetchIncomeData();
        });
    });

    // 初始加载数据
    fetchIncomeData();
});

function fetchIncomeData() {
    const ctx = document.getElementById('incomeTrendChart');
    ctx.style.display = 'none';
    document.getElementById('noIncomeData').style.display = 'none';

    // 显示加载状态
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = `
        <div class="spinner"></div>
        <p>正在加载数据...</p>
    `;
    ctx.parentNode.insertBefore(loadingDiv, ctx);

    fetch(`/admin/income_analysis/data/?period=${incomeConfig.currentPeriod}`)
        .then(handleResponse)
        .then(processIncomeData)
        .catch(handleError)
        .finally(() => {
            // 移除加载状态
            if (loadingDiv.parentNode) {
                loadingDiv.parentNode.removeChild(loadingDiv);
            }
        });
}

function handleResponse(response) {
    if (!response.ok) {
        throw new Error(`请求失败: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

function processIncomeData(data) {
    console.log('API响应数据:', data);

    if (!data || !data.success) {
        showNoIncomeDataMessage();
        return;
    }

    // 更新统计数据
    updateStats(data.stats);

    // 更新时间段标题
    updateStatsTitle(data);

    // 渲染图表
    if (data.trend && data.trend.labels && data.trend.labels.length > 0) {
        renderIncomeTrendChart(data.trend);
    } else {
        document.getElementById('incomeTrendChart').style.display = 'none';
        document.getElementById('noIncomeData').style.display = 'flex';
    }
}

function updateStats(stats) {
    if (!stats) return;

    document.getElementById('totalIncome').textContent = `${formatMoney(stats.total_income)} 元`;
    document.getElementById('avgDailyIncome').textContent = `${formatMoney(stats.avg_daily_income)} 元`;
    document.getElementById('maxDailyIncome').textContent = `${formatMoney(stats.max_daily_income)} 元`;
    document.getElementById('parkingCount').textContent = `${stats.parking_count || 0} 次`;
}

function updateStatsTitle(data) {
    const periodMap = {
        'today': '今日', 'week': '本周', 'month': '本月',
        'quarter': '本季度', 'year': '本年'
    };

    let dateRange = '';
    if (data.trend?.labels?.length > 0) {
        const start = data.trend.labels[0];
        const end = data.trend.labels[data.trend.labels.length - 1];
        dateRange = `(${start}至${end})`;
    }

    document.getElementById('statsTitle').textContent =
        `${periodMap[incomeConfig.currentPeriod]}统计数据 ${dateRange}`;
}

function renderIncomeTrendChart(trendData) {
    const ctx = document.getElementById('incomeTrendChart');
    const noDataDiv = document.getElementById('noIncomeData');

    if (!trendData || !trendData.labels || trendData.labels.length === 0) {
        ctx.style.display = 'none';
        noDataDiv.style.display = 'flex';
        return;
    }

    ctx.style.display = 'block';
    noDataDiv.style.display = 'none';

    if (incomeConfig.incomeTrendChart) {
        incomeConfig.incomeTrendChart.destroy();
    }

    // 根据时间段设置不同的图表配置
    let xTitle = '时间';
    if (incomeConfig.currentPeriod === 'today') {
        xTitle = '小时';
    } else if (incomeConfig.currentPeriod === 'week' || incomeConfig.currentPeriod === 'month') {
        xTitle = '日期';
    } else if (incomeConfig.currentPeriod === 'quarter' || incomeConfig.currentPeriod === 'year') {
        xTitle = '月份';
    }

    incomeConfig.incomeTrendChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: trendData.labels,
            datasets: [{
                label: '收入金额 (元)',
                data: trendData.amounts,
                backgroundColor: 'rgba(24, 144, 255, 0.7)',
                borderColor: 'rgba(24, 144, 255, 1)',
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: 'rgba(24, 144, 255, 0.9)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 20,
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 14
                    },
                    callbacks: {
                        label: (context) => ` ${context.dataset.label}: ${context.raw.toFixed(2)}元`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '金额 (元)',
                        padding: {top: 10, bottom: 10},
                        font: {
                            size: 14
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: xTitle,
                        padding: {top: 10, bottom: 10},
                        font: {
                            size: 14
                        }
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

function showNoIncomeDataMessage() {
    document.getElementById('totalIncome').textContent = '0 元';
    document.getElementById('avgDailyIncome').textContent = '0 元';
    document.getElementById('maxDailyIncome').textContent = '0 元';
    document.getElementById('parkingCount').textContent = '0 次';

    document.getElementById('incomeTrendChart').style.display = 'none';
    document.getElementById('noIncomeData').style.display = 'flex';
}

function handleError(error) {
    console.error('获取收入数据错误:', error);
    showNoIncomeDataMessage();

    // 开发环境下使用模拟数据
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log("使用模拟数据进行展示");
        useSampleIncomeData();
    }
}

function useSampleIncomeData() {
    // 仅用于开发环境的模拟数据
    const sampleData = {
        success: true,
        stats: {
            total_income: 3560.50,
            avg_daily_income: 518.68,
            max_daily_income: 890.00,
            parking_count: 42
        },
        trend: {
            labels: ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
            amounts: [450, 620, 380, 890, 540, 710, 560]
        }
    };

    processIncomeData(sampleData);
}