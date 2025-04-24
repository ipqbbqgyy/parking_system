 document.addEventListener('DOMContentLoaded', function() {
        fetch('/admin/admin_logs/data/', {  // 修改为正确的API端点
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'  // 明确声明期望JSON响应
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const tableBody = document.querySelector('#admin-logs-table tbody');
                const loadingIndicator = document.getElementById('loading-indicator');

                if (data.logs.length === 0) {
                    loadingIndicator.innerHTML = '<p>暂无日志记录</p>';
                    return;
                }

                data.logs.forEach(log => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${log.timestamp}</td>
                        <td>${log.username}</td>
                        <td>${log.action}</td>
                        <td>${log.content_type || '-'}</td>
                        <td>${log.object_id || '-'}</td>
                        <td>${log.message}</td>
                    `;
                    tableBody.appendChild(row);
                });

                loadingIndicator.style.display = 'none';
            } else {
                alert('加载日志失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加载日志时发生错误');
        });
    });