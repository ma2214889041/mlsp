let deferredPrompt;

// 检查是否已经安装
function isPWAInstalled() {
    // 检查是否处于standalone模式
    if (window.matchMedia('(display-mode: standalone)').matches || 
        window.matchMedia('(display-mode: fullscreen)').matches || 
        window.navigator.standalone === true) {
        return true;
    }
    
    // 检查localStorage中的标记
    if (localStorage.getItem('pwaInstalled') === 'true') {
        return true;
    }
    
    return false;
}

// 立即显示安装横幅
function showInstallBanner() {
    // 如果已经安装或者之前拒绝过且时间不超过12小时，不显示
    const lastDismissed = localStorage.getItem('pwaInstallDismissed');
    if (isPWAInstalled() || (lastDismissed && (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60) < 12)) {
        return;
    }
    
    // 创建安装横幅
    const installBanner = document.createElement('div');
    installBanner.className = 'install-banner';
    installBanner.id = 'pwa-install-banner';
    installBanner.style.position = 'fixed';
    installBanner.style.bottom = '0';
    installBanner.style.left = '0';
    installBanner.style.right = '0';
    installBanner.style.backgroundColor = '#fff';
    installBanner.style.boxShadow = '0 -2px 10px rgba(0,0,0,0.2)';
    installBanner.style.padding = '15px 20px';
    installBanner.style.display = 'flex';
    installBanner.style.justifyContent = 'space-between';
    installBanner.style.alignItems = 'center';
    installBanner.style.zIndex = '9999';
    
    // 根据页面类型选择不同的图标和文字
    let appName = "米兰食品系统";
    let appIcon = "📱"; // 默认图标
    if (window.location.pathname.includes('/client')) {
        appName = "米兰客户端";
        appIcon = "🍽️";
    } else if (window.location.pathname.includes('/admin')) {
        appName = "米兰管理端";
        appIcon = "📊";
    } else if (window.location.pathname.includes('/employee')) {
        appName = "米兰仓库端";
        appIcon = "📦";
    }
    
    // 设置横幅内容
    installBanner.innerHTML = `
        <div style="display:flex; align-items:center;">
            <div style="font-size:2em; margin-right:15px;">${appIcon}</div>
            <div>
                <div style="font-weight:bold;margin-bottom:5px;">将${appName}添加到主屏幕</div>
                <div style="font-size:0.9em;color:#666;">安装应用以获得更佳体验</div>
            </div>
        </div>
        <div>
            <button id="install-pwa-button" class="btn btn-danger">安装应用</button>
            <button id="dismiss-pwa-button" class="btn btn-outline-secondary ms-2">稍后再说</button>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(installBanner);
    
    // 处理安装按钮点击
    const installButton = document.getElementById('install-pwa-button');
    if (installButton) {
        installButton.addEventListener('click', async () => {
            if (deferredPrompt) {
                // 隐藏安装横幅
                installBanner.style.display = 'none';
                
                // 显示浏览器安装提示
                deferredPrompt.prompt();
                
                // 等待用户响应
                const { outcome } = await deferredPrompt.userChoice;
                console.log(`用户安装选择: ${outcome}`);
                
                if (outcome === 'accepted') {
                    localStorage.setItem('pwaInstalled', 'true');
                }
                
                // 重置安装提示
                deferredPrompt = null;
            } else {
                // 如果没有deferredPrompt（例如在iOS上），显示手动安装指南
                showInstallGuide();
            }
        });
    }
    
    // 处理关闭按钮点击
    const dismissButton = document.getElementById('dismiss-pwa-button');
    if (dismissButton) {
        dismissButton.addEventListener('click', () => {
            installBanner.style.display = 'none';
            localStorage.setItem('pwaInstallDismissed', Date.now().toString());
        });
    }
}

// 显示手动安装指南
function showInstallGuide() {
    // 创建模态对话框
    const installGuide = document.createElement('div');
    installGuide.className = 'modal fade';
    installGuide.id = 'installGuideModal';
    installGuide.setAttribute('tabindex', '-1');
    installGuide.setAttribute('aria-hidden', 'true');
    
    // 判断设备类型
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /android/i.test(navigator.userAgent);
    const isChrome = /chrome/i.test(navigator.userAgent);
    
    let installInstructions = '';
    
    if (isIOS) {
        installInstructions = `
            <ol class="mt-3">
                <li>点击浏览器底部的<strong>分享按钮</strong> <i class="bi bi-box-arrow-up"></i></li>
                <li>滚动并选择<strong>"添加到主屏幕"</strong></li>
                <li>点击右上角的<strong>"添加"</strong>按钮</li>
            </ol>
        `;
    } else if (isAndroid && isChrome) {
        installInstructions = `
            <ol class="mt-3">
                <li>点击地址栏右侧的<strong>菜单按钮</strong> <i class="bi bi-three-dots-vertical"></i></li>
                <li>选择<strong>"安装应用"</strong>或<strong>"添加到主屏幕"</strong></li>
                <li>点击<strong>"安装"</strong>按钮确认</li>
            </ol>
        `;
    } else {
        installInstructions = `
            <ol class="mt-3">
                <li>点击浏览器菜单 <i class="bi bi-three-dots-vertical"></i></li>
                <li>选择<strong>"安装应用"</strong>或<strong>"添加到主屏幕"</strong></li>
                <li>按照提示完成安装</li>
            </ol>
        `;
    }
    
    installGuide.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">如何安装应用</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>请按照以下步骤将此应用添加到您的主屏幕：</p>
                    ${installInstructions}
                    <div class="alert alert-success mt-3">
                        <i class="bi bi-info-circle"></i> 安装后，您可以从主屏幕启动应用，获得全屏体验！
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(installGuide);
    
    // 显示模态对话框
    var modal = new bootstrap.Modal(document.getElementById('installGuideModal'));
    modal.show();
}

// 监听beforeinstallprompt事件
window.addEventListener('beforeinstallprompt', (e) => {
    // 阻止Chrome 67+自动显示安装提示
    e.preventDefault();
    
    // 保存事件以便稍后触发
    deferredPrompt = e;
    
    // 显示自定义安装提示
    showInstallBanner();
});

// 监听appinstalled事件
window.addEventListener('appinstalled', (evt) => {
    // 应用被安装后，记录状态并隐藏安装横幅
    localStorage.setItem('pwaInstalled', 'true');
    
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.style.display = 'none';
    }
    
    // 清除deferredPrompt
    deferredPrompt = null;
    
    // 显示安装成功消息
    const successToast = document.createElement('div');
    successToast.className = 'toast align-items-center text-white bg-success border-0 position-fixed top-0 end-0 m-3';
    successToast.style.zIndex = '9999';
    successToast.setAttribute('role', 'alert');
    successToast.setAttribute('aria-live', 'assertive');
    successToast.setAttribute('aria-atomic', 'true');
    
    successToast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-check-circle-fill me-2"></i> 应用已成功安装！
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(successToast);
    
    // 显示通知
    const bsToast = new bootstrap.Toast(successToast, {
        delay: 3000
    });
    bsToast.show();
    
    // 几秒后移除元素
    setTimeout(() => {
        successToast.remove();
    }, 3500);
});

// 页面加载完成后检查安装状态并显示提示
document.addEventListener('DOMContentLoaded', () => {
    // 延迟2秒显示安装提示，避免影响页面加载体验
    setTimeout(() => {
        // 如果有deferredPrompt，使用它；否则检查是否需要显示安装指南
        if (deferredPrompt) {
            showInstallBanner();
        } else if (!isPWAInstalled()) {
            // 通过用户代理判断是否需要显示安装指南
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
            
            // 在iOS或非Chrome浏览器上，可能需要手动安装指南
            if (isIOS || !isChrome) {
                // 检查是否已经拒绝过安装
                const lastDismissed = localStorage.getItem('pwaInstallDismissed');
                if (!lastDismissed || (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60) >= 12) {
                    showInstallBanner();
                }
            }
        }
    }, 2000);
});
