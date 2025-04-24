// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 绑定隐私政策链接点击事件
    document.getElementById('footer-privacy-link').addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('privacy-modal').style.display = 'flex';
    });

    // 绑定服务条款链接点击事件
    document.getElementById('footer-terms-link').addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('terms-modal').style.display = 'flex';
    });

    // 为所有关闭按钮添加点击事件
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });

    // 初始化聊天机器人
    initChatBot();
});

/**
 * 初始化聊天机器人功能
 */
function initChatBot() {
    let chatClient = null;
    let isInitialized = false;
    const chatButton = document.getElementById('chat-button');
    const chatLoading = document.getElementById('chat-loading');

    // 显示加载动画
    chatLoading.style.display = 'flex';

    // 预加载聊天SDK
    const preloadIframe = document.createElement('iframe');
    preloadIframe.style.display = 'none';
    preloadIframe.src = 'https://coze.com';
    document.body.appendChild(preloadIframe);

    // 初始化聊天SDK
    chatClient = new CozeWebSDK.WebChatClient({
        config: {
            bot_id: '7496461509561385011',
            lazy_load: false,
        },
        componentProps: {
            title: '凉心停车助手',
            welcome_message: '您好！我是凉心停车助手，有什么可以帮您的吗？',
        },
        auth: {
            type: 'token',
            token: 'pat_4zqDq4rpkBkNeKODkEcpi9z5uztmBO3nwlxIYs3NjYQTs9Zg2fujawMr0athRKYz',
            onRefreshToken: function() {
                return 'pat_4zqDq4rpkBkNeKODkEcpi9z5uztmBO3nwlxIYs3NjYQTs9Zg2fujawMr0athRKYz';
            }
        },
        onReady: function() {
            // SDK加载完成后的回调
            chatLoading.style.display = 'none';
            chatButton.style.display = 'flex';
            isInitialized = true;
            preloadIframe.parentNode.removeChild(preloadIframe);
        }
    });

    // 聊天按钮点击事件
    chatButton.addEventListener('click', function() {
        if (!isInitialized) {
            alert('聊天功能正在加载中，请稍候...');
            return;
        }
        chatClient.isOpen() ? chatClient.close() : chatClient.open();
    });
}