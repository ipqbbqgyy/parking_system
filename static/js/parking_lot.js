// parking_lot.js - 凉心停车场车位管理脚本
document.addEventListener('DOMContentLoaded', function () {
    // 全局变量
    const state = {
        currentSpotNumber: null,
        currentLicensePlate: null,
        currentVehicleType: null
    };

    // DOM元素
    const elements = {
        promotionBanner: document.getElementById('promotionBanner'),
        errorToast: document.getElementById('errorToast'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        timeInputModal: document.getElementById('timeInputModal'),
        reservationTime: document.getElementById('reservationTime')
    };

    // 初始化应用
    function init() {
        bindEvents();
        refreshSpots();
        setInterval(refreshSpots, 60000); // 每分钟自动刷新
    }

    // 绑定事件
    function bindEvents() {
        document.querySelectorAll('.spot').forEach(spot => {
            spot.addEventListener('click', handleSpotClick);
        });
    }

    // 显示加载状态
    function showLoading(show) {
        elements.loadingIndicator.style.display = show ? 'block' : 'none';
    }

    // 显示错误提示
    function showError(message, duration = 3000) {
        elements.errorToast.textContent = message;
        elements.errorToast.style.display = 'block';
        setTimeout(() => {
            elements.errorToast.style.display = 'none';
        }, duration);
    }

    // 刷新车位状态
    function refreshSpots() {
        showLoading(true);

        fetch('/parking_lot/data/')
            .then(handleResponse)
            .then(data => {
                updateSpotStatus(data.spots);
                updatePromotionBanner(data.active_promotion);
            })
            .catch(error => {
                console.error('刷新车位失败:', error);
                showError('车位状态更新失败，请稍后重试');
            })
            .finally(() => showLoading(false));
    }

    // 处理响应
    function handleResponse(response) {
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }
        return response.json();
    }

    // 更新车位状态
    function updateSpotStatus(spotsData) {
        document.querySelectorAll('.spot').forEach(spot => {
            const spotId = spot.getAttribute('data-spot-id');
            const spotData = spotsData.find(s => s.id === spotId);
            const status = spotData?.status || 'available';

            // 更新类名
            spot.className = `spot ${spotId} ${status} S`;

            // 更新状态文本
            const statusText = spot.querySelector('.status-text') ||
                spot.appendChild(document.createElement('span'));
            statusText.className = 'status-text';

            if (status === "reserved") {
                statusText.textContent = '已预订';
            } else if (status === "occupied") {
                statusText.textContent = '占用';
            } else {
                statusText.textContent = '可用';
            }
        });
    }

// 更新促销信息
function updatePromotionBanner(promotion) {
    if (promotion?.name) {
        // 格式化时间
        const startTime = new Date(promotion.start_time).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        const endTime = new Date(promotion.end_time).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        elements.promotionBanner.innerHTML = `
            <div>当前促销活动: ${promotion.name} - ${promotion.discount}</div>
            <div>活动时间: ${startTime} 至 ${endTime}</div>
        `;
        elements.promotionBanner.style.display = 'block';
    } else {
        elements.promotionBanner.style.display = 'none';
    }
}

    // 车位点击处理
    function handleSpotClick() {
        state.currentSpotNumber = this.getAttribute('data-spot-id');
        const action = toHalfWidth(prompt(`请选择操作：\n1. 预订车位\n2. 使用车位\n\n输入 1 或 2：`));

        if (action === null || action.trim() === '') return;

        if (action === "1") {
            handleReservation();
        } else if (action === "2") {
            handleParking();
        } else {
            showError('无效的选择，请输入1或2');
        }
    }

    // 处理预订
    function handleReservation() {
        const licensePlate = prompt(`请输入车牌号以预订车位 ${state.currentSpotNumber}:
        例如：京A12345`);
        if (!licensePlate) return;

        validateLicensePlate(licensePlate)
            .then(() => {
                state.currentLicensePlate = licensePlate;
                return selectVehicleType();
            })
            .then(type => {
                state.currentVehicleType = type;
                showTimePicker();
            })
            .catch(error => showError(error));
    }

    // 处理停车
    function handleParking() {
        const licensePlate = prompt(`请输入车牌号以停入车位 ${state.currentSpotNumber}:
        例如：京A12345`);
        if (!licensePlate) return;

        validateLicensePlate(licensePlate)
            .then(() => selectVehicleType())
            .then(type => parkVehicle(licensePlate, type))
            .catch(error => showError(error));
    }

    // 车牌验证
    function validateLicensePlate(licensePlate) {
        return new Promise((resolve, reject) => {
            if (!licensePlate) return reject('车牌号不能为空');

            fetch('/validate_license_plate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `license_plate=${encodeURIComponent(licensePlate)}`
            })
            .then(handleResponse)
            .then(data => data.success ? resolve() : reject(data.message))
            .catch(() => reject('验证车牌时发生错误'));
        });
    }

    // 选择车辆类型
    function selectVehicleType() {
        return new Promise((resolve) => {
            const type = toHalfWidth(prompt(`请选择车辆类型：\n1. 小型汽车\n2. 货车\n3. 新能源车\n\n输入 1、2 或 3：`));

            if (type === "1") resolve("car");
            else if (type === "2") resolve("truck");
            else if (type === "3") resolve("ev");
            else {
                showError('无效的车辆类型，自动选择小型汽车');
                resolve("car");
            }
        });
    }

    // 显示时间选择器
    function showTimePicker() {
        elements.timeInputModal.style.display = 'block';
        elements.reservationTime.value = '';
    }

    // 提交预订
    window.submitReservationTime = function() {
        const useTime = elements.reservationTime.value;
        if (!useTime || !isValidDateTime(useTime)) {
            showError('请输入有效的预定使用时间');
            return;
        }

        const formData = new URLSearchParams();
        formData.append('spot_number', state.currentSpotNumber);
        formData.append('license_plate', state.currentLicensePlate);
        formData.append('vehicle_type', state.currentVehicleType);
        formData.append('reservation_use_time', useTime);

        showLoading(true);

        fetch('/reserve_spot/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                alert('预订成功！');
                refreshSpots();
                setTimeout(() => window.location.href = "/we/", 1500);
            } else {
                showError(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('预订失败，请重试');
        })
        .finally(() => {
            showLoading(false);
            elements.timeInputModal.style.display = 'none';
        });
    };

    // 取消时间输入
    window.cancelReservationTime = function() {
        elements.timeInputModal.style.display = 'none';
    };

    // 停车操作
    function parkVehicle(licensePlate, vehicleType) {
        showLoading(true);

        fetch('/entry/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `license_plate=${encodeURIComponent(licensePlate)}&spot_number=${encodeURIComponent(state.currentSpotNumber)}&vehicle_type=${encodeURIComponent(vehicleType)}`
        })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                alert('车辆入场成功！');
                refreshSpots();
                setTimeout(() => window.location.href = "/we/", 1500);
            } else {
                showError(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('停车失败，请重试');
        })
        .finally(() => showLoading(false));
    }

    // 辅助函数：验证日期时间
    function isValidDateTime(dateTime) {
        return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(dateTime);
    }

    // 辅助函数：全角转半角
    function toHalfWidth(input) {
        return input?.replace(/[\uff01-\uff5e]/g, char =>
            String.fromCharCode(char.charCodeAt(0) - 0xfee0)
        ) || '';
    }

    // 辅助函数：获取CSRF令牌
    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) return decodeURIComponent(value);
        }
        return null;
    }

    // 启动应用
    init();
});