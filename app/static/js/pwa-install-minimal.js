document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    // 检查是否已安装
    if (window.matchMedia('(display-mode: standalone)').matches || 
        window.matchMedia('(display-mode: fullscreen)').matches || 
        window.navigator.standalone === true) {
      console.log('应用已以PWA模式安装');
      return;
    }
    
    // 检查是否最近关闭过安装提示
    const lastDismissed = localStorage.getItem('pwaInstallDismissed');
    if (lastDismissed && (Date.now() - parseInt(lastDismissed)) / (1000 * 60 * 60) < 12) {
      return;
    }
    
    // 创建安装横幅
    const installBanner = document.createElement('div');
    installBanner.style.position = 'fixed';
    installBanner.style.bottom = '0';
    installBanner.style.left = '0';
    installBanner.style.right = '0';
    installBanner.style.padding = '15px 20px';
    installBanner.style.background = 'white';
    installBanner.style.boxShadow = '0 -2px 10px rgba(0,0,0,0.2)';
    installBanner.style.display = 'flex';
    installBanner.style.justifyContent = 'space-between';
    installBanner.style.alignItems = 'center';
    installBanner.style.zIndex = '9999';
    
    // 根据当前URL确定是哪个应用
    let appName = "米兰应用";
    if (window.location.href.includes('/client')) {
      appName = "米兰客户端";
    } else if (window.location.href.includes('/admin')) {
      appName = "米兰管理端";
    } else if (window.location.href.includes('/employee')) {
      appName = "米兰仓库端";
    }
    
    // 设置横幅内容
    installBanner.innerHTML = `
      <div style="display:flex; align-items:center;">
        <div style="font-size:2em; margin-right:15px;">📱</div>
        <div>
          <div style="font-weight:bold;margin-bottom:5px;">将${appName}添加到主屏幕</div>
          <div style="font-size:0.9em;color:#666;">安装应用以获得更佳体验</div>
        </div>
      </div>
      <div>
        <button id="install-pwa-guide" class="btn btn-danger">安装方法</button>
        <button id="dismiss-pwa" class="btn btn-outline-secondary ms-2">稍后再说</button>
      </div>
    `;
    
    document.body.appendChild(installBanner);
    
    // 处理"安装方法"按钮点击
    document.getElementById('install-pwa-guide').addEventListener('click', () => {
      // 检测设备类型
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const isAndroid = /Android/.test(navigator.userAgent);
      
      // 创建指南模态框
      const modal = document.createElement('div');
      modal.className = 'modal fade';
      modal.id = 'installGuideModal';
      modal.setAttribute('tabindex', '-1');
      
      let instructions = '';
      
      if (isIOS) {
        instructions = `
          <ol class="mt-3">
            <li>点击Safari底部的<strong>分享按钮</strong> <i class="bi bi-share"></i></li>
            <li>在菜单中选择<strong>"添加到主屏幕"</strong></li>
            <li>点击<strong>"添加"</strong>确认</li>
          </ol>
          <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> 注意：请使用Safari浏览器访问本网站，其他浏览器不支持添加到主屏幕。
          </div>
        `;
      } else if (isAndroid) {
        instructions = `
          <ol class="mt-3">
            <li>点击Chrome右上角的<strong>菜单按钮</strong> <i class="bi bi-three-dots-vertical"></i></li>
            <li>选择<strong>"安装应用"</strong>或<strong>"添加到主屏幕"</strong></li>
            <li>按照提示完成安装</li>
          </ol>
        `;
      } else {
        instructions = `
          <ol class="mt-3">
            <li>点击浏览器右上角的<strong>菜单按钮</strong></li>
            <li>选择<strong>"安装应用"</strong>或<strong>"添加到主屏幕"</strong></li>
            <li>按照提示完成安装</li>
          </ol>
          <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> 在某些浏览器中，您也可以点击地址栏右侧的安装图标。
          </div>
        `;
      }
      
      modal.innerHTML = `
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">如何安装${appName}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <p>请按照以下步骤将应用添加到主屏幕：</p>
              ${instructions}
              <div class="alert alert-success mt-3">
                <i class="bi bi-check-circle"></i> 安装后，您可以从主屏幕直接启动应用，享受全屏体验！
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      // 显示模态框
      const bsModal = new bootstrap.Modal(document.getElementById('installGuideModal'));
      bsModal.show();
      
      // 模态框关闭后移除DOM元素
      document.getElementById('installGuideModal').addEventListener('hidden.bs.modal', function () {
        document.body.removeChild(modal);
      });
    });
    
    // 处理"稍后再说"按钮点击
    document.getElementById('dismiss-pwa').addEventListener('click', () => {
      document.body.removeChild(installBanner);
      localStorage.setItem('pwaInstallDismissed', Date.now().toString());
    });
  }, 2000); // 延迟2秒显示
});
