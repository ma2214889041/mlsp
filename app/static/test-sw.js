// 非常简单的Service Worker
self.addEventListener('install', (event) => {
  console.log('Test Service Worker installed!');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Test Service Worker activated!');
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  console.log('Fetching:', event.request.url);
  event.respondWith(fetch(event.request));
});
