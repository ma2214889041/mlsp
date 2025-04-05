// Service Worker注册
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/mlsp/static/sw.js', {
      scope: '/mlsp/'
    }).then(registration => {
      console.log('ServiceWorker 注册成功，作用域: ', registration.scope);
    }).catch(error => {
      console.log('ServiceWorker 注册失败: ', error);
    });
    
    // 检查是否可以安装PWA
    window.addEventListener('beforeinstallprompt', (e) => {
      // 保存安装事件
      window.deferredPrompt = e;
      console.log('可以安装PWA!');
      
      // 显示安装按钮
      setTimeout(() => {
        const installBtn = document.createElement('button');
        installBtn.textContent = '安装应用';
        installBtn.className = 'btn btn-warning position-fixed bottom-0 end-0 m-3';
        installBtn.style.zIndex = '9999';
        installBtn.onclick = () => {
          if (window.deferredPrompt) {
            window.deferredPrompt.prompt();
            window.deferredPrompt.userChoice.then(result => {
              console.log('用户安装选择: ' + result.outcome);
              window.deferredPrompt = null;
              document.body.removeChild(installBtn);
            });
          }
        };
        document.body.appendChild(installBtn);
      }, 2000);
    });
  });
}
