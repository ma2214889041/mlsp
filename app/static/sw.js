// 米兰食品公司Service Worker
const CACHE_NAME = 'milan-food-cache-v3';

// 安装事件
self.addEventListener('install', event => {
  console.log('Service Worker 安装中...');
  self.skipWaiting();
});

// 激活事件
self.addEventListener('activate', event => {
  console.log('Service Worker 激活中...');
  event.waitUntil(self.clients.claim());
});

// 拦截fetch请求
self.addEventListener('fetch', event => {
  // 简单地传递请求
  event.respondWith(fetch(event.request).catch(() => {
    return new Response('离线模式 - 请检查网络连接');
  }));
});
