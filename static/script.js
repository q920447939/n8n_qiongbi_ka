// 使用jQuery简化代码
$(document).ready(function () {
    // 初始化所有功能
    initTabs();
    initModals();
    createParticles();
    initQRCodeAnimation();
    initAmountTextSizing();
    initOrderButtons();

    // 初始化统计功能
    window.statsManager = new StatsManager();
});

// 统计数据管理类
class StatsManager {
    constructor() {
        this.isAnimating = false;
        this.init();
    }

    init() {
        // 启动动画显示数据
        this.startAnimations();
    }

    // 启动数字动画
    startAnimations() {
        if (this.isAnimating) return;
        this.isAnimating = true;

        this.animateNumber('#visit-count', $('#visit-count').text(), 3000);
        this.animateNumber('#daily_orders', $('#daily_orders').text(), 3000);
    }
    // 数字滚动动画（改进版）
    animateNumber(selector, targetNumber, duration = 2000) {
        const element = document.querySelector(selector);
        if (!element) return;

        const startNumber = 0;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // 使用缓动函数创造更自然的动画效果
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const currentNumber = Math.floor(startNumber + (targetNumber - startNumber) * easeOutCubic);

            element.textContent = this.formatNumber(currentNumber);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = this.formatNumber(targetNumber);
            }
        };

        requestAnimationFrame(animate);
    }

    // 数字格式化
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
        return num.toString();
    }




    // 平滑更新数字
    smoothUpdateNumber(selector, newValue) {
        const element = document.querySelector(selector);
        if (!element) return;

        const currentValue = this.parseNumberFromText(element.textContent);
        if (currentValue < newValue) {
            this.animateNumber(selector, newValue, 800);
        }
    }

    // 从文本中解析数字
    parseNumberFromText(text) {
        const cleanText = text.replace(/[,M]/g, '');
        const num = parseFloat(cleanText);
        return isNaN(num) ? 0 : num;
    }


}

// 初始化标签页切换功能 - 使用jQuery简化
function initTabs() {
    $('.tab-btn').on('click', function () {
        // 移除所有活动状态
        $('.tab-btn').removeClass('active');
        $('.tab-content').removeClass('active');

        // 添加当前活动状态
        $(this).addClass('active');
        const tabId = $(this).data('tab');
        $('#' + tabId).addClass('active');
    });
}


// 初始化所有模态框 - 使用jQuery简化
function initModals() {
    // 初始化二维码模态框
    initQRModal();

    // 初始化反馈模态框
    initFeedbackModal();

    // 初始化立即办理模态框
    initOrderModal();
}

// 初始化二维码模态框
function initQRModal() {
    const modal = $('#qr-modal');
    const btn = $('#feedback-btn');
    const closeBtn = $('#qr-close');

    btn.on('click', () => {
        modal.addClass('show');
        $('body').addClass('modal-open');
    });

    closeBtn.on('click', () => {
        modal.removeClass('show');
        $('body').removeClass('modal-open');
    });

    $(window).on('click', (e) => {
        if (e.target === modal[0]) {
            modal.removeClass('show');
            $('body').removeClass('modal-open');
        }
    });
}

// 初始化反馈模态框
function initFeedbackModal() {
    // 反馈模态框逻辑
}

// 初始化立即办理模态框
function initOrderModal() {
    const modal = $('#order-modal');
    const closeBtn = $('#order-close');

    $(document).on('click', '.order-btn', function () {
        const cardId = $(this).data('card-id');
        loadOrderButtons(cardId);
        modal.addClass('show');
        $('body').addClass('modal-open');
    });

    closeBtn.on('click', () => {
        modal.removeClass('show');
        $('body').removeClass('modal-open');
    });

    $(window).on('click', (e) => {
        if (e.target === modal[0]) {
            modal.removeClass('show');
            $('body').removeClass('modal-open');
        }
    });
}


// 创建粒子效果 - 使用jQuery简化
function createParticles() {
    const $header = $('header');
    const $particles = $('<div class="particles"></div>');

    const colors = [
        'rgba(30, 136, 229, 0.2)', 'rgba(255, 152, 0, 0.2)',
        'rgba(0, 177, 88, 0.2)', 'rgba(235, 97, 0, 0.2)'
    ];

    // 添加15个粒子
    for (let i = 0; i < 15; i++) {
        const size = Math.random() * 30 + 10;
        const $particle = $('<div class="particle"></div>').css({
            width: `${size}px`,
            height: `${size}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            backgroundColor: colors[Math.floor(Math.random() * colors.length)],
            animationDelay: `${Math.random() * 5}s`
        });

        $particles.append($particle);
    }

    $header.append($particles);
}

// 初始化二维码动画 - 使用jQuery简化
function initQRCodeAnimation() {
    const $qrCode = $('#qr-code');

    if ($qrCode.length === 0) return;

    // 添加脉冲动画
    setInterval(() => {
        $qrCode.css('animation', 'pulse 1s');
        setTimeout(() => {
            $qrCode.css('animation', '');
        }, 1000);
    }, 5000);
}

// 初始化金额文本大小调整
function initAmountTextSizing() {
    $('.amount').each(function () {
        const text = $(this).text().trim();
        if (text.length > 8) {
            $(this).addClass('very-long-text');
        } else if (text.length > 5) {
            $(this).addClass('long-text');
        }
    });
}

// 初始化订单按钮事件
function initOrderButtons() {
    $(document).on('click', '.btn-order', function (e) {
        e.preventDefault();

        // 获取卡片信息
        const $card = $(this).closest('.card');
        const cardId = $(this).data('id');
        const operator = $card.find('.operator-tag').text();
        const price = $card.find('.amount').text();
        const productName = $card.find('.card-name').text();

        // 存储当前卡片信息到全局变量，供模态框使用
        window.currentCardInfo = {
            id: cardId,
            operator: operator,
            price: price,
            productName: productName
        };

        // 显示立即办理模态框并加载对应的按钮配置
        showOrderModal();
        loadOrderButtonsConfig(cardId);
    });
}

// 显示立即办理模态框
function showOrderModal() {
    const $orderModal = $('#order-modal');
    $orderModal.addClass('show').fadeIn(300);
    $orderModal.find('.modal-content').css('opacity', '0').animate({ opacity: 1 }, 300);
}

// 加载立即办理按钮配置
function loadOrderButtonsConfig(cardId) {
    if (!cardId) return;

    const url = `/card/api/order-buttons?card_id=${cardId}`;

    $.ajax({
        url: url,
        method: 'GET',
        success: function (response) {
            if (response.code == 200 && response.data) {
                //console.log('成功获取按钮配置:', response.data);
                renderOrderButtons(response.data);
            } else {
                //console.error('获取按钮配置失败:', response.message);
                // 如果获取配置失败，显示默认按钮
                renderOrderButtons([
                    { text: '立即办理', url: '#' }
                ]);
            }
        },
        error: function (xhr, status, error) {
            //console.error('请求按钮配置失败:', error);
            alert('网络错误，请稍后再试');
            // 如果请求失败，显示默认按钮
            /* renderOrderButtons([
                { text: '立即办理', url: '#' }
            ]); */
        }
    });
}

// 渲染立即办理按钮
function renderOrderButtons(buttons) {
    const $container = $('#order-buttons-container');
    $container.empty();

    if (buttons.length === 0) {
        // 如果没有配置按钮，显示默认按钮
        buttons = [{ text: '立即办理', url: '#' }];
    }

    // 根据按钮数量设置容器样式
    if (buttons.length === 1) {
        $container.addClass('single-button').removeClass('multiple-buttons');
    } else {
        $container.addClass('multiple-buttons').removeClass('single-button');
    }

    // 生成按钮HTML
    buttons.forEach(function (button) {
        const $button = $('<a>', {
            href: button.url,
            class: 'order-action-btn',
            text: button.text,
            target: '_blank',
            click: function (e) {
                // 如果URL是#，阻止默认行为
                if (button.url === '#') {
                    e.preventDefault();
                    showToast('功能开发中，敬请期待！');
                }
            }
        });

        $container.append($button);
    });
}

// 显示提示信息的通用函数
function showToast(message) {
    const $toast = $('#success-toast');
    $toast.find('span').text(message);
    $toast.addClass('show');
    setTimeout(() => {
        $toast.removeClass('show');
    }, 3000);
}

// 页面卸载时清理资源
$(window).on('beforeunload', function () {
    if (window.statsManager) {
        window.statsManager.destroy();
    }
});
