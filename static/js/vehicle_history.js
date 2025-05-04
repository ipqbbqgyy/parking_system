// 显示或隐藏返回顶部按钮
window.addEventListener('scroll', function() {
    const backToTop = document.querySelector('.back-to-top');
    if (window.pageYOffset > 300) {
        backToTop.classList.add('visible');
    } else {
        backToTop.classList.remove('visible');
    }
});

// 平滑滚动到顶部
document.querySelector('.back-to-top').addEventListener('click', function(e) {
    e.preventDefault();
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// 添加卡片动画
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.vehicle-card');
    cards.forEach((card, index) => {
        // 添加延迟动画
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});