// 客户端PWA安装脚本
let deferredPrompt;

// 检测是否可以安装PWA
window.addEventListener('beforeinstallprompt', (e) => {
  // 阻止Chrome自动显示安装提示
  e.preventDefault();
  
  // 保存事件以便稍后触发
  deferredPrompt = e;
  
  // 创建安装按钮
  const installBtn = document.createElement('button');
  installBtn.textContent = '安装客户端应用';
  installBtn.className = 'btn btn-danger position-fixed bottom-0 end-0 m-3';
  installBtn.style.zIndex = '9999';
  installBtn.id = 'pwa-install-btn';
  
  // 添加点击事件
  installBtn.addEventListener('click', () => {
    // 隐藏按钮
    installBtn.style.display = 'none';
    
    // 显示安装提示
    deferredPrompt.prompt();
    
    // 等待用户响应
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('用户接受安装');
      } else {
        console.log('用户拒绝安装');
        // 如果用户拒绝，可以再次显示按钮
        installBtn.style.display = 'block';
      }
      
      // 清除提示
      deferredPrompt = null;
    });
  });
  
  // 如果页面已有安装按钮，则不再添加
  if (!document.getElementById('pwa-install-btn')) {
    document.body.appendChild(installBtn);
  }
});

// 检测PWA是否已安装
window.addEventListener('appinstalled', (evt) => {
  console.log('客户端应用已安装');
  // 移除安装按钮
  const installBtn = document.getElementById('pwa-install-btn');
  if (installBtn) {
    installBtn.remove();
  }
});
