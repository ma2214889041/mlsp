// 仓库端Service Worker
const CACHE_NAME = 'milan-employee-cache-v1';
const urlsToCache = [
  '/mlsp/employee/',
  '/mlsp/employee/dashboard',
  '/mlsp/employee/scan',
  '/mlsp/static/employee-manifest.json',
  '/mlsp/static/icons/employee.png'
];

// 安装事件
self.addEventListener('install', event => {
  console.log('仓库端Service Worker 安装中...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('缓存已打开');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// 激活事件
self.addEventListener('activate', event => {
  console.log('仓库端Service Worker 激活中...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('milan-employee-')) {
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
        if (response) {
          return response;
        }
        
        return fetch(event.request)
          .then(response => {
            if(!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            var responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
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
  const title = '米兰仓库端';
  const options = {
    body: event.data ? event.data.text() : '有新任务',
    icon: '/mlsp/static/icons/employee.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});
