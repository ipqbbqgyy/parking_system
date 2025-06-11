document.addEventListener('DOMContentLoaded', function() {
    // 滚动效果
    window.addEventListener('scroll', function() {
        document.body.classList.toggle('scrolled', window.scrollY > 10);
    });

    // 注销功能
    document.getElementById('logout-btn')?.addEventListener('click', function() {
        fetch("{% url 'admin:logout' %}", {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'csrfmiddlewaretoken={{ csrf_token }}'
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        });
    });
});