// 全局配置
const config = {
    areaChart: null,
    durationChart: null,
    currentRange: 'today' // 默认显示今天的数据
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化统计卡片动画
    initStatCards();

    // 绑定时间范围按钮事件
    initTimeRangeButtons();

    // 初始加载数据
    fetchParkingData();
});

// 初始化统计卡片动画
function initStatCards() {
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('show');
        }, index * 200);
    });
}

// 初始化时间范围按钮
function initTimeRangeButtons() {
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 更新按钮状态
            document.querySelectorAll('.time-range-btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');

            // 更新当前时间范围并重新获取数据
            config.currentRange = this.dataset.range;
            fetchParkingData();
        });
    });
}

// 从API获取停车数据
function fetchParkingData() {
    showLoadingState(true);

    fetch(`/admin/parking_analysis/data/?period=${config.currentRange}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data?.success) {
                if (data.vehicles?.length > 0) {
                    processData(data.vehicles);
                } else {
                    showNoDataMessage();
                }
            } else {
                throw new Error('Invalid data format');
            }
        })
        .catch(error => {
            console.error('获取数据错误:', error);
            useSampleData();
        })
        .finally(() => {
            showLoadingState(false);
        });
}

// 显示/隐藏加载状态
function showLoadingState(show) {
    const loadingElement = document.getElementById('loadingIndicator') || createLoadingElement();
    loadingElement.style.display = show ? 'block' : 'none';
}

// 创建加载指示器元素
function createLoadingElement() {
    const loader = document.createElement('div');
    loader.id = 'loadingIndicator';
    loader.style.display = 'none';
    loader.style.position = 'fixed';
    loader.style.top = '50%';
    loader.style.left = '50%';
    loader.style.transform = 'translate(-50%, -50%)';
    loader.style.padding = '15px';
    loader.style.background = 'rgba(0,0,0,0.7)';
    loader.style.color = 'white';
    loader.style.borderRadius = '5px';
    loader.style.zIndex = '1000';
    loader.textContent = '数据加载中...';
    document.body.appendChild(loader);
    return loader;
}

// 处理数据
function processData(vehicles) {
    try {
        hideNoDataMessages();

        // 处理每辆车的数据
        const processedData = vehicles.map(vehicle => {
            const entryTime = new Date(vehicle.entry_time);
            const exitTime = vehicle.exit_time ? new Date(vehicle.exit_time) : null;

            // 计算停车时长（分钟）
            const duration = exitTime ?
                Math.round((exitTime - entryTime) / (1000 * 60)) :
                Math.round((new Date() - entryTime) / (1000 * 60));

            // 提取区域 (A, B, C, D, E)
            const area = vehicle.spot_number ?
                vehicle.spot_number.charAt(0).toUpperCase() : '未知';

            return {
                license_plate: vehicle.license_plate,
                spot_number: vehicle.spot_number,
                entry_time: vehicle.entry_time,
                exit_time: vehicle.exit_time,
                entryTime: entryTime,
                exitTime: exitTime,
                duration: duration,
                area: area,
                status: exitTime ? '已出库' : '未出库'
            };
        });

        // 计算统计数据
        calculateStatistics(processedData);

        // 渲染图表
        renderCharts(processedData);
    } catch (e) {
        console.error('数据处理错误:', e);
        useSampleData();
    }
}

// 计算统计数据
function calculateStatistics(data) {
    // 过滤出已出库的车辆（有离开时间的）
    const exitedVehicles = data.filter(v => v.exitTime);

    // 计算统计数据
    const totalCount = data.length;
    const avgDuration = exitedVehicles.length > 0 ?
        Math.round(exitedVehicles.reduce((sum, v) => sum + v.duration, 0) / exitedVehicles.length) : 0;
    const maxDuration = exitedVehicles.length > 0 ?
        Math.max(...exitedVehicles.map(v => v.duration)) : 0;
    const minDuration = exitedVehicles.length > 0 ?
        Math.min(...exitedVehicles.map(v => v.duration)) : 0;

    // 更新统计卡片
    updateStatCard('totalCount', totalCount);
    updateStatCard('avgDuration', exitedVehicles.length > 0 ? `${avgDuration} 分钟` : '暂无');
    updateStatCard('maxDuration', exitedVehicles.length > 0 ? `${maxDuration} 分钟` : '暂无');
    updateStatCard('minDuration', exitedVehicles.length > 0 ? `${minDuration} 分钟` : '暂无');
}

// 更新统计卡片
function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        // 添加动画效果
        element.classList.add('stat-updated');
        setTimeout(() => element.classList.remove('stat-updated'), 500);
    }
}

// 渲染图表
function renderCharts(data) {
    // 按区域统计
    const areaCounts = {};
    data.forEach(vehicle => {
        areaCounts[vehicle.area] = (areaCounts[vehicle.area] || 0) + 1;
    });

    // 按时长统计
    const durationData = {
        '0-30分钟': 0,
        '30-60分钟': 0,
        '1-2小时': 0,
        '2-3小时': 0,
        '3小时以上': 0
    };

    data.forEach(vehicle => {
        const duration = vehicle.duration;
        if (duration <= 30) durationData['0-30分钟']++;
        else if (duration <= 60) durationData['30-60分钟']++;
        else if (duration <= 120) durationData['1-2小时']++;
        else if (duration <= 180) durationData['2-3小时']++;
        else durationData['3小时以上']++;
    });

    // 渲染区域图表
    renderAreaChart(areaCounts);

    // 渲染时长图表
    renderDurationChart(durationData);
}

// 渲染区域图表
function renderAreaChart(data) {
    const ctx = document.getElementById('areaChart');
    const noDataDiv = document.getElementById('noChartData');

    // 检查是否有数据
    if (Object.keys(data).length === 0) {
        ctx.style.display = 'none';
        noDataDiv.style.display = 'block';
        return;
    }

    ctx.style.display = 'block';
    noDataDiv.style.display = 'none';

    // 销毁旧图表（如果存在）
    if (config.areaChart !== null) {
        config.areaChart.destroy();
        config.areaChart = null;
    }

    // 按区域字母排序
    const sortedAreas = Object.keys(data).sort();
    const areaLabels = sortedAreas.map(area => `${area}区`);
    const areaValues = sortedAreas.map(area => data[area]);

    // 创建新图表
    config.areaChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: areaLabels,
            datasets: [{
                label: '停车数量',
                data: areaValues,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '车辆数量'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '停车区域'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `各区域停车数量分布 (${getRangeTitle(config.currentRange)})`,
                    font: {
                        size: 16
                    }
                }
            }
        }
    });
}

// 渲染时长图表
function renderDurationChart(data) {
    const ctx = document.getElementById('durationChart');
    const noDataDiv = document.getElementById('noDurationData');

    // 检查是否有数据
    const total = Object.values(data).reduce((a, b) => a + b, 0);
    if (total === 0) {
        ctx.style.display = 'none';
        noDataDiv.style.display = 'block';
        return;
    }

    ctx.style.display = 'block';
    noDataDiv.style.display = 'none';

    // 销毁旧图表（如果存在）
    if (config.durationChart !== null) {
        config.durationChart.destroy();
        config.durationChart = null;
    }

    // 创建新图表
    config.durationChart = new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `停车时长分布 (${getRangeTitle(config.currentRange)})`,
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// 获取时间范围标题
function getRangeTitle(range) {
    const titles = {
        'today': '今日',
        'week': '本周',
        'month': '本月',
        'quarter': '本季度',
        'year': '本年',
        'all': '全部'
    };
    return titles[range] || range;
}

// 显示无数据消息
function showNoDataMessage() {
    document.getElementById('noChartData').style.display = 'block';
    document.getElementById('noDurationData').style.display = 'block';
}

// 隐藏无数据消息
function hideNoDataMessages() {
    document.getElementById('noChartData').style.display = 'none';
    document.getElementById('noDurationData').style.display = 'none';
}

// 使用模拟数据
function useSampleData() {
    console.log('使用模拟数据进行展示');
    hideNoDataMessages();

    // 生成模拟数据
    const sampleData = generateSampleData();
    processData(sampleData);
}

// 生成模拟数据
function generateSampleData() {
    const now = new Date();
    const sampleVehicles = [];
    const areas = ['A', 'B', 'C', 'D', 'E'];

    // 生成20条模拟数据
    for (let i = 0; i < 20; i++) {
        const area = areas[Math.floor(Math.random() * areas.length)];
        const entryTime = new Date(now);
        entryTime.setHours(now.getHours() - Math.floor(Math.random() * 24));
        entryTime.setMinutes(now.getMinutes() - Math.floor(Math.random() * 60));

        const exitTime = new Date(entryTime);
        exitTime.setHours(entryTime.getHours() + Math.floor(Math.random() * 5));
        exitTime.setMinutes(entryTime.getMinutes() + Math.floor(Math.random() * 60));

        sampleVehicles.push({
            license_plate: `京A${Math.floor(1000 + Math.random() * 9000)}`,
            spot_number: `${area}${Math.floor(1 + Math.random() * 50)}`,
            entry_time: entryTime.toISOString(),
            exit_time: exitTime.toISOString(),
            duration: Math.round((exitTime - entryTime) / (1000 * 60))
        });
    }

    return sampleVehicles;
}