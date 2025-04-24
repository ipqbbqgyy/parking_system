   // 人机验证逻辑
        document.addEventListener('DOMContentLoaded', function() {
            const thumb = document.getElementById('slider-thumb');
            const track = document.getElementById('slider-track');
            const fill = document.getElementById('slider-fill');
            const valueDisplay = document.getElementById('slider-value');
            const hiddenInput = document.getElementById('slider_value');
            const successMsg = document.getElementById('verification-success');
            const registerButton = document.getElementById('register-button');

            let isDragging = false;

            thumb.addEventListener('mousedown', function(e) {
                isDragging = true;
                document.addEventListener('mousemove', onDrag);
                document.addEventListener('mouseup', stopDrag);
            });

            function onDrag(e) {
                if (!isDragging) return;

                const trackRect = track.getBoundingClientRect();
                let newLeft = e.clientX - trackRect.left;

                // 限制在轨道范围内
                newLeft = Math.max(0, Math.min(newLeft, trackRect.width));

                const percentage = Math.round((newLeft / trackRect.width) * 100);

                // 更新UI
                thumb.style.left = `${newLeft}px`;
                fill.style.width = `${percentage}%`;
                valueDisplay.textContent = `${percentage}%`;
                hiddenInput.value = percentage;

                // 验证成功
                if (percentage === 100) {
                    successMsg.style.display = 'block';
                    registerButton.disabled = false;
                } else {
                    successMsg.style.display = 'none';
                    registerButton.disabled = true;
                }
            }

            function stopDrag() {
                isDragging = false;
                document.removeEventListener('mousemove', onDrag);
                document.removeEventListener('mouseup', stopDrag);
            }

            // 触摸支持
            thumb.addEventListener('touchstart', function(e) {
                isDragging = true;
                document.addEventListener('touchmove', onTouchDrag);
                document.addEventListener('touchend', stopTouchDrag);
            });

            function onTouchDrag(e) {
                if (!isDragging) return;

                const trackRect = track.getBoundingClientRect();
                let newLeft = e.touches[0].clientX - trackRect.left;

                newLeft = Math.max(0, Math.min(newLeft, trackRect.width));

                const percentage = Math.round((newLeft / trackRect.width) * 100);

                thumb.style.left = `${newLeft}px`;
                fill.style.width = `${percentage}%`;
                valueDisplay.textContent = `${percentage}%`;
                hiddenInput.value = percentage;

                if (percentage === 100) {
                    successMsg.style.display = 'block';
                    registerButton.disabled = false;
                } else {
                    successMsg.style.display = 'none';
                    registerButton.disabled = true;
                }
            }

            function stopTouchDrag() {
                isDragging = false;
                document.removeEventListener('touchmove', onTouchDrag);
                document.removeEventListener('touchend', stopTouchDrag);
            }

            // 原有模态框代码保持不变
            document.getElementById('form-privacy-link').addEventListener('click', function(e) {
                e.preventDefault();
                openModal('privacy-modal');
            });

            document.getElementById('form-terms-link').addEventListener('click', function(e) {
                e.preventDefault();
                openModal('terms-modal');
            });

            function openModal(modalId) {
                const modal = document.getElementById(modalId);
                modal.style.display = 'flex';
            }

            function closeModal(modalId) {
                const modal = document.getElementById(modalId);
                modal.style.display = 'none';
            }
        });