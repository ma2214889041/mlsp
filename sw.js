// 在根目录使用的简单 Service Worker
const CACHE_NAME = 'milan-food-cache-v2';
const urlsToCache = [
  '/mlsp/',
  '/mlsp/client',
  '/mlsp/admin',
  '/mlsp/employee',
  '/mlsp/static/client-manifest.json',
  '/mlsp/static/admin-manifest.json',
  '/mlsp/static/employee-manifest.json'
];

self.addEventListener('install', event => {
  console.log('Service Worker 安装中...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('缓存已打开');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('Service Worker 激活中...');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  console.log('拦截请求:', event.request.url);
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

self.addEventListener('push', event => {
  const title = '米兰食品公司';
  const options = {
    body: event.data ? event.data.text() : '有新消息',
    icon: '/mlsp/static/icons/client.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});
