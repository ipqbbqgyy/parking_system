    // 轮播图功能
    document.addEventListener('DOMContentLoaded', function() {
        const slides = document.querySelectorAll('.hero-slide');
        let currentSlide = 0;

        function showSlide(n) {
            // 隐藏所有幻灯片
            slides.forEach(slide => {
                slide.classList.remove('active');
            });

            // 显示当前幻灯片
            slides[n].classList.add('active');
        }

        function nextSlide() {
            currentSlide = (currentSlide + 1) % slides.length;
            showSlide(currentSlide);
        }

        // 初始显示第一张
        showSlide(currentSlide);

        // 每5秒切换一次
        setInterval(nextSlide, 5000);

        // 动态调整客服窗口位置
        function adjustChatPosition() {
            const chatContainer = document.querySelector('.chat-container');
            if (chatContainer) {
                const windowHeight = window.innerHeight;
                const chatHeight = chatContainer.offsetHeight;

                if (windowHeight - chatHeight < 120) {
                    chatContainer.style.bottom = `${windowHeight - chatHeight - 20}px`;
                } else {
                    chatContainer.style.bottom = '120px';
                }
            }
        }

        // 监听窗口大小变化
        window.addEventListener('resize', adjustChatPosition);

        // 页面加载时调整位置
        window.addEventListener('load', adjustChatPosition);
    });