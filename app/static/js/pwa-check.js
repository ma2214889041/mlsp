// 存储安装事件
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // 阻止Chrome自动显示安装提示
  e.preventDefault();
  
  // 存储事件供以后触发
  deferredPrompt = e;
  
  console.log('检测到可安装PWA!');
  
  // 显示自定义安装按钮
  const installBtn = document.createElement('button');
  installBtn.id = 'pwa-install-btn';
  installBtn.innerText = '安装应用';
  installBtn.style.position = 'fixed';
  installBtn.style.bottom = '20px';
  installBtn.style.right = '20px';
  installBtn.style.backgroundColor = '#dc3545';
  installBtn.style.color = 'white';
  installBtn.style.padding = '10px 20px';
  installBtn.style.borderRadius = '5px';
  installBtn.style.border = 'none';
  installBtn.style.zIndex = '9999';
  installBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
  
  installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) {
      return;
    }
    
    // 显示安装提示
    deferredPrompt.prompt();
    
    // 等待用户响应
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`用户选择: ${outcome}`);
    
    // 无论结果如何，我们不能再次使用该事件
    deferredPrompt = null;
    
    // 隐藏按钮
    installBtn.style.display = 'none';
  });
  
  document.body.appendChild(installBtn);
});

// 检测PWA已安装
window.addEventListener('appinstalled', () => {
  console.log('PWA已成功安装');
  // 隐藏任何安装按钮
  const installBtn = document.getElementById('pwa-install-btn');
  if (installBtn) {
    installBtn.style.display = 'none';
  }
  
  // 显示已安装通知
  const toast = document.createElement('div');
  toast.style.position = 'fixed';
  toast.style.top = '20px';
  toast.style.right = '20px';
  toast.style.backgroundColor = '#28a745';
  toast.style.color = 'white';
  toast.style.padding = '10px 20px';
  toast.style.borderRadius = '5px';
  toast.style.zIndex = '9999';
  toast.innerText = '应用已成功安装！';
  
  document.body.appendChild(toast);
  
  // 3秒后移除通知
  setTimeout(() => {
    document.body.removeChild(toast);
  }, 3000);
});
