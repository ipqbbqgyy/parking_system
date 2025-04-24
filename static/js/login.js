document.addEventListener('DOMContentLoaded', function() {
    console.log('Login script loaded'); // 调试日志

    const elements = {
        thumb: document.getElementById('slider-thumb'),
        track: document.getElementById('slider-track'),
        fill: document.getElementById('slider-fill'),
        valueDisplay: document.getElementById('slider-value'),
        hiddenInput: document.getElementById('slider_value'),
        successMsg: document.getElementById('verification-success'),
        loginButton: document.getElementById('login-button'),
        loginForm: document.getElementById('login-form'),
        errorContainer: document.getElementById('error-container')
    };

    let isDragging = false;
    elements.loginButton.disabled = true;

    // 错误处理函数
    const showError = (message) => {
        console.log('显示错误:', message); // 调试日志
        elements.errorContainer.innerHTML = `
            <div class="error-message" style="display: none;">
                ${message}
            </div>
        `;
        const errorDiv = elements.errorContainer.firstElementChild;
        errorDiv.style.display = 'block';
        setTimeout(() => errorDiv.style.opacity = 1, 10);
    };

    // 滑块处理逻辑
    const handleDrag = (clientX) => {
        const trackRect = elements.track.getBoundingClientRect();
        let newLeft = Math.max(0, Math.min(clientX - trackRect.left, trackRect.width));
        const percentage = Math.round((newLeft / trackRect.width) * 100);

        elements.thumb.style.left = `${newLeft}px`;
        elements.fill.style.width = `${percentage}%`;
        elements.valueDisplay.textContent = `${percentage}%`;
        elements.hiddenInput.value = percentage;

        if (percentage === 100) {
            elements.successMsg.style.display = 'block';
            elements.loginButton.disabled = false;
            elements.track.classList.remove('shake');
        } else {
            elements.successMsg.style.display = 'none';
            elements.loginButton.disabled = true;
        }
    };

    // 事件监听器
    const initEventListeners = () => {
        // 鼠标事件
        elements.thumb.addEventListener('mousedown', () => {
            isDragging = true;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', stopDrag);
        });

        // 触摸事件
        elements.thumb.addEventListener('touchstart', (e) => {
            isDragging = true;
            document.addEventListener('touchmove', onTouchMove);
            document.addEventListener('touchend', stopDrag);
        });

        // 表单提交
        elements.loginForm.addEventListener('submit', function(e) {
            console.log('提交时滑块值:', elements.hiddenInput.value); // 调试日志
            if (elements.hiddenInput.value !== '100') {
                e.preventDefault();
                showError('请完成人机验证！');
                elements.track.classList.add('shake');
                setTimeout(() => elements.track.classList.remove('shake'), 1000);
            }
        });
    };

    // 事件处理函数
    const onMouseMove = (e) => isDragging && handleDrag(e.clientX);
    const onTouchMove = (e) => isDragging && handleDrag(e.touches[0].clientX);

    const stopDrag = () => {
        isDragging = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('touchmove', onTouchMove);
        document.removeEventListener('mouseup', stopDrag);
        document.removeEventListener('touchend', stopDrag);
    };

    initEventListeners();
});