// 米兰食品系统Service Worker
const CACHE_NAME = 'milan-pwa-cache-v2';
const urlsToCache = [
  '/mlsp/',
  '/mlsp/client/',
  '/mlsp/admin/',
  '/mlsp/employee/',
  '/mlsp/static/client-manifest.json',
  '/mlsp/static/admin-manifest.json',
  '/mlsp/static/employee-manifest.json',
  '/mlsp/static/icons/client.png',
  '/mlsp/static/icons/admin.png',
  '/mlsp/static/icons/employee.png'
];

// 安装Service Worker
self.addEventListener('install', event => {
  console.log('Service Worker 安装中...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('缓存已打开');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// 激活Service Worker
self.addEventListener('activate', event => {
  console.log('Service Worker 激活中...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('milan-')) {
            console.log('清除旧缓存:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    .then(() => self.clients.claim())
  );
});

// 处理fetch请求
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // 如果在缓存中找到了匹配的响应，则返回它
        if (response) {
          return response;
        }
        
        // 否则，去网络获取资源
        return fetch(event.request)
          .then(response => {
            // 检查是否收到有效的响应
            if(!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // 克隆响应，因为响应是流，只能使用一次
            var responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                // 不缓存API请求和动态内容
                if (!event.request.url.includes('/api/')) {
                  console.log('缓存资源:', event.request.url);
                  cache.put(event.request, responseToCache);
                }
              });
            
            return response;
          });
      })
  );
});

// 处理推送通知
self.addEventListener('push', event => {
  console.log('收到推送通知');
  const title = '米兰食品公司';
  const options = {
    body: event.data ? event.data.text() : '有新消息',
    icon: '/mlsp/static/icons/client.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('message', event => {
  console.log('Service Worker 收到消息:', event.data);
});
