// we.js - 凉心智慧停车系统个人中心功能脚本
(function() {
    // ===== 通用函数 =====

    // 获取 Cookie 的函数
    window.getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    // ===== 预订功能 =====

    // 使用预订车位
    window.useReservation = function(reservationId) {
        const csrfToken = getCookie('csrftoken');
        fetch(`/use_reservation/${reservationId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if(data.redirect_url){
                window.location.href = data.redirect_url;
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('操作失败，请重试');
        });
    };

    // 取消预订
    window.cancelReservation = function(reservationId) {
        if (!confirm('确定要取消这个预订吗？')) return;
        const csrfToken = getCookie('csrftoken');
        fetch(`/cancel_reservation/${reservationId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if(data.redirect_url){
                window.location.href = data.redirect_url;
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('取消失败，请重试');
        });
    };

    // ===== 支付功能 =====

    // 显示支付模态框
    window.showPaymentModal = function(vehicleId) {
        const csrfToken = getCookie('csrftoken');

        // 显示加载状态
        document.getElementById('paymentDetails').innerHTML = '<p>加载中，请稍候...</p>';
        document.getElementById('paymentModal').style.display = 'block';

        fetch(`/exit_vehicle/${vehicleId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.text();
        })
        .then(html => {
            document.getElementById('paymentDetails').innerHTML = html;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('paymentDetails').innerHTML = `
                <div class="error-message">
                    <p>加载支付信息失败</p>
                    <p>${error.message}</p>
                    <button onclick="showPaymentModal(${vehicleId})">重试</button>
                </div>
            `;
        });
    };

    // 关闭支付模态框
    window.closePaymentModal = function() {
        document.getElementById('paymentModal').style.display = 'none';
    };

    // 处理支付提交
    window.submitPayment = function(vehicleId) {
        const csrfToken = getCookie('csrftoken');

        // 显示处理中状态
        const submitBtn = document.querySelector('#paymentDetails button[onclick^="submitPayment"]');
        if(submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = '处理中...';
        }

        fetch(`/payment/${vehicleId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin',
            body: JSON.stringify({})
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('支付成功！');
                location.reload();
            } else {
                alert(data.message || '支付失败');
                if(submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '确认支付';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('发生错误: ' + error.message);
            if(submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = '确认支付';
            }
        });
    };

    // ===== 反馈功能 =====

    // 显示反馈模态框
    document.addEventListener('DOMContentLoaded', function() {
        const feedbackBtn = document.getElementById('feedbackBtn');
        if(feedbackBtn) {
            feedbackBtn.addEventListener('click', function(e) {
                e.preventDefault();
                document.getElementById('feedbackModal').style.display = 'block';
            });
        }
    });

    // 关闭反馈模态框
    window.closeFeedbackModal = function() {
        document.getElementById('feedbackModal').style.display = 'none';
    };

    // 提交反馈表单
    document.addEventListener('DOMContentLoaded', function() {
        const feedbackForm = document.getElementById('feedbackForm');
        if(feedbackForm) {
            feedbackForm.addEventListener('submit', function(e) {
                e.preventDefault();

                const feedbackType = document.getElementById('feedbackType').value;
                const feedbackContent = document.getElementById('feedbackContent').value;

                if (!feedbackType || !feedbackContent) {
                    alert('请填写完整的反馈信息');
                    return;
                }

                const csrfToken = getCookie('csrftoken');
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;

                submitBtn.disabled = true;
                submitBtn.textContent = '提交中...';

                fetch('/submit_feedback/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        feedback_type: feedbackType,
                        content: feedbackContent
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('感谢您的反馈！');
                        closeFeedbackModal();
                        document.getElementById('feedbackType').value = '';
                        document.getElementById('feedbackContent').value = '';
                    } else {
                        alert('提交反馈失败: ' + (data.message || '未知错误'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('提交反馈时出错，请重试');
                })
                .finally(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                });
            });
        }
    });

    // 获取反馈记录
    window.getFeedbackHistory = function() {
        const csrfToken = getCookie('csrftoken');
        const feedbackHistoryBtn = document.getElementById('feedbackHistoryBtn');

        if(feedbackHistoryBtn) {
            feedbackHistoryBtn.disabled = true;
            const originalText = feedbackHistoryBtn.textContent;
            feedbackHistoryBtn.textContent = '加载中...';
        }

        fetch('/feedback_history/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const modalId = 'feedbackHistoryModal-' + Date.now();
                const modal = document.createElement('div');
                modal.className = 'modal';
                modal.id = modalId;
                modal.style.display = 'block';

                let content = `
                    <div class="modal-content">
                        <span class="close" onclick="closeModalById('${modalId}')">&times;</span>
                        <h2>我的反馈记录</h2>
                        <div class="feedback-history-container">
                `;

                if (data.feedbacks && data.feedbacks.length > 0) {
                    content += `
                        <table class="feedback-table">
                            <thead>
                                <tr>
                                    <th>反馈类型</th>
                                    <th>反馈内容</th>
                                    <th>提交时间</th>
                                    <th>处理状态</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    data.feedbacks.forEach(feedback => {
                        content += `
                            <tr>
                                <td>${feedback.feedback_type_display || feedback.feedback_type}</td>
                                <td>${feedback.content}</td>
                                <td>${feedback.created_at}</td>
                                <td>${feedback.is_resolved ? '已处理' : '待处理'}</td>
                            </tr>
                        `;
                    });

                    content += `
                            </tbody>
                        </table>
                    `;
                } else {
                    content += '<p>暂无反馈记录</p>';
                }

                content += `
                        </div>
                    </div>
                `;

                modal.innerHTML = content;
                document.getElementById('modals-container').appendChild(modal);

                modal.addEventListener('click', function(event) {
                    if (event.target === modal) {
                        modal.remove();
                    }
                });
            } else {
                alert('获取反馈记录失败: ' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('获取反馈记录时出错: ' + error.message);
        })
        .finally(() => {
            if(feedbackHistoryBtn) {
                feedbackHistoryBtn.disabled = false;
                feedbackHistoryBtn.textContent = originalText;
            }
        });
    };

    // 关闭模态框函数
    window.closeModalById = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.remove();
        }
    };

    // 绑定反馈记录按钮点击事件
    document.addEventListener('DOMContentLoaded', function() {
        const feedbackHistoryBtn = document.getElementById('feedbackHistoryBtn');
        if(feedbackHistoryBtn) {
            feedbackHistoryBtn.addEventListener('click', function(e) {
                e.preventDefault();
                getFeedbackHistory();
            });
        }
    });

    // 点击模态框外部关闭模态框
    window.addEventListener('click', function(event) {
        const paymentModal = document.getElementById('paymentModal');
        const feedbackModal = document.getElementById('feedbackModal');

        if (event.target == paymentModal) {
            closePaymentModal();
        }
        if (event.target == feedbackModal) {
            closeFeedbackModal();
        }
    });

    // 为操作按钮添加交互效果
    document.addEventListener('DOMContentLoaded', function() {
        const actionButtons = document.querySelectorAll('.profile-actions a, .exit-button');

        actionButtons.forEach(btn => {
            btn.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(1px)';
            });

            btn.addEventListener('mouseup', function() {
                this.style.transform = 'translateY(0)';
            });

            btn.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    });

})();