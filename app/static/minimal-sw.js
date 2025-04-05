// 最小化的Service Worker
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

// 不缓存任何内容，但仍能接收推送通知
self.addEventListener('push', event => {
  const title = '米兰食品公司';
  const options = {
    body: event.data ? event.data.text() : '有新消息',
    icon: '/static/icons/client-192.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});
