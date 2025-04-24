// 全局配置
const config = {
    areaChart: null,
    durationChart: null
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化统计卡片动画
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('show');
        }, index * 200);
    });

    fetchParkingData();
});

// 从API获取停车数据
function fetchParkingData() {
    fetch('/admin/parking_analysis/data/')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常，状态码: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success && data.vehicles && data.vehicles.length > 0) {
                processData(data.vehicles);
            } else {
                showNoDataMessage();
            }
        })
        .catch(error => {
            console.error('获取数据错误:', error);
            useSampleData();
        });
}

// 处理数据
function processData(vehicles) {
    try {
        // 处理每辆车的数据
        const processedData = vehicles.map(vehicle => {
            const entryTime = new Date(vehicle.entry_time);
            const exitTime = vehicle.exit_time ? new Date(vehicle.exit_time) : null;

            // 计算停车时长（分钟）
            const duration = exitTime ?
                Math.round((exitTime - entryTime) / (1000 * 60)) :
                Math.round((new Date() - entryTime) / (1000 * 60));

            // 提取区域 (A, B, C, D, E)
            const area = vehicle.spot_number ? vehicle.spot_number.charAt(0).toUpperCase() : '未知';

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
    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('avgDuration').textContent = exitedVehicles.length > 0 ?
        `${avgDuration.toFixed(1)} 分钟` : '暂无';
    document.getElementById('maxDuration').textContent = exitedVehicles.length > 0 ?
        `${maxDuration} 分钟` : '暂无';
    document.getElementById('minDuration').textContent = exitedVehicles.length > 0 ?
        `${minDuration} 分钟` : '暂无';
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
            maintainAspectRatio: false
        }
    });
}

// 显示无数据消息
function showNoDataMessage() {
    document.getElementById('noChartData').style.display = 'block';
    document.getElementById('noDurationData').style.display = 'block';
}

// 使用模拟数据
function useSampleData() {
    console.log('使用模拟数据进行展示');

    const sampleData = {
        vehicles: [
            {
                license_plate: "京A23456",
                spot_number: "B1",
                entry_time: "2025-03-28T09:09:46",
                exit_time: "2025-03-28T09:12:15"
            },
            {
                license_plate: "京A98765",
                spot_number: "C2",
                entry_time: "2025-03-28T09:10:08",
                exit_time: "2025-03-28T09:12:34"
            },
            {
                license_plate: "京P00000",
                spot_number: "D3",
                entry_time: "2025-03-28T09:10:18",
                exit_time: null
            }
        ]
    };

    if (sampleData.vehicles && sampleData.vehicles.length > 0) {
        processData(sampleData.vehicles);
    } else {
        showNoDataMessage();
    }
}