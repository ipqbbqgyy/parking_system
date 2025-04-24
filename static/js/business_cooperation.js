        // 当用户滚动页面时，显示或隐藏“回到顶部”按钮
        window.onscroll = function() {
            scrollFunction();
        };

        function scrollFunction() {
            var backToTopButton = document.getElementById("back-to-top");
            if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                backToTopButton.style.display = "block";
            } else {
                backToTopButton.style.display = "none";
            }
        }

        // 当用户点击按钮时，回到页面顶部
        document.getElementById("back-to-top").onclick = function() {
            document.body.scrollTop = 0; // 对于 Safari
            document.documentElement.scrollTop = 0; // 对于 Chrome, Firefox, IE 和 Opera
        };