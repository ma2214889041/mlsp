if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/mlsp/sw.js')
      .then(function(registration) {
        console.log('Service Worker 注册成功，作用域为: ', registration.scope);
      })
      .catch(function(error) {
        console.log('Service Worker 注册失败: ', error);
      });
  });
}
