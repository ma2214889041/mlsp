// 检测是否在PWA模式下运行
document.addEventListener('DOMContentLoaded', function() {
  if (window.matchMedia('(display-mode: fullscreen)').matches || 
      window.matchMedia('(display-mode: standalone)').matches || 
      window.navigator.standalone === true) {
    
    // 在PWA模式下运行
    console.log('在PWA模式下运行');
    
    // 为导航栏添加刷新按钮
    const navbarDiv = document.querySelector('.navbar-nav');
    if (navbarDiv) {
      const refreshButton = document.createElement('a');
      refreshButton.className = 'nav-link pwa-refresh-button';
      refreshButton.href = '#';
      refreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> 刷新';
      refreshButton.addEventListener('click', function(e) {
        e.preventDefault();
        window.location.reload();
      });
      
      navbarDiv.appendChild(refreshButton);
    }
    
    // 监听网络状态变化
    window.addEventListener('online', function() {
      console.log('恢复在线状态');
      // 显示在线通知
      showNetworkToast('已恢复网络连接', 'success');
    });
    
    window.addEventListener('offline', function() {
      console.log('网络已断开');
      // 显示离线通知
      showNetworkToast('网络已断开连接', 'danger');
    });
    
    // 添加网络状态通知
    function showNetworkToast(message, type) {
      const toast = document.createElement('div');
      toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
      toast.setAttribute('role', 'alert');
      toast.setAttribute('aria-live', 'assertive');
      toast.setAttribute('aria-atomic', 'true');
      toast.style.zIndex = '9999';
      
      toast.innerHTML = `
        <div class="d-flex">
          <div class="toast-body">
            ${message}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      `;
      
      document.body.appendChild(toast);
      
      // 显示toast
      const bsToast = new bootstrap.Toast(toast, {
        delay: 3000
      });
      bsToast.show();
      
      // 设置自动移除
      setTimeout(() => {
        toast.remove();
      }, 3500);
    }
  }
});
