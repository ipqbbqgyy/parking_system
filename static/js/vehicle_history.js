        // 显示或隐藏返回顶部按钮
        window.onscroll = function() {
            const backToTopButton = document.querySelector('.back-to-top');
            if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                backToTopButton.style.display = 'block';
            } else {
                backToTopButton.style.display = 'none';
            }
        };

        // 点击返回顶部按钮
        document.querySelector('.back-to-top').addEventListener('click', function(event) {
            event.preventDefault();  // 阻止默认跳转行为
            document.body.scrollTop = 0;  // 兼容 Safari
            document.documentElement.scrollTop = 0;  // 兼容 Chrome, Firefox, IE, Opera
        });