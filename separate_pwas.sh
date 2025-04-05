#!/bin/bash

echo "开始配置三个独立的PWA..."

# 1. 修改FastAPI应用，添加特定路径的Service Worker
cat > /home/mlsp/app/main.py << 'EOL'
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/mlsp/app_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# 创建应用
app = FastAPI(title="米兰食品公司订单与仓储系统")

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = f"URL: {request.url}, Method: {request.method}, Error: {str(exc)}, Traceback: {traceback.format_exc()}"
    logger.error(error_detail)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请联系管理员", "error": str(exc)}
    )

# 确保静态目录存在
os.makedirs("/home/mlsp/app/static/qrcodes/shelves", exist_ok=True)
os.makedirs("/home/mlsp/app/static/qrcodes/slots", exist_ok=True)
os.makedirs("/home/mlsp/app/static/uploads/order_photos", exist_ok=True)
os.makedirs("/home/mlsp/app/static/uploads/products", exist_ok=True)

# 设置所有目录权限
for path in ["/home/mlsp/app/static", "/home/mlsp/app/static/qrcodes", 
             "/home/mlsp/app/static/uploads", "/home/mlsp/app/static/qrcodes/shelves",
             "/home/mlsp/app/static/qrcodes/slots", "/home/mlsp/app/static/uploads/order_photos",
             "/home/mlsp/app/static/uploads/products"]:
    os.system(f"chmod -R 777 {path}")

# 创建数据库表
logger.info("创建数据库表...")
from app.db import models, database
models.Base.metadata.create_all(bind=database.engine)
logger.info("数据库表创建完成")

# Service Worker路由 - 每个模块使用独立的Service Worker
@app.get("/client/sw.js")
async def get_client_service_worker():
    return FileResponse("/home/mlsp/app/static/client-sw.js")

@app.get("/admin/sw.js")
async def get_admin_service_worker():
    return FileResponse("/home/mlsp/app/static/admin-sw.js")

@app.get("/employee/sw.js")
async def get_employee_service_worker():
    return FileResponse("/home/mlsp/app/static/employee-sw.js")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="/home/mlsp/app/static"), name="static")

# 导入并注册路由
logger.info("注册路由...")
from app.api.endpoints.client import router as client_router
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.common import router as common_router
from app.api.endpoints.employee import router as employee_router
from app.api.endpoints.inventory import router as inventory_router

# 这里修改路由注册顺序和前缀，确保inventory_router在admin_router之前注册
app.include_router(common_router)
app.include_router(client_router, prefix="/client", tags=["client"])
app.include_router(inventory_router, tags=["inventory"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(employee_router, prefix="/employee", tags=["employee"])
logger.info("路由注册完成")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
EOL

# 2. 创建三个不同的Service Worker文件，作用域限制在各自的路径
echo "创建三个Service Worker文件..."

# 客户端Service Worker
cat > /home/mlsp/app/static/client-sw.js << 'EOL'
// 客户端Service Worker
const CACHE_NAME = 'milan-client-cache-v1';
const urlsToCache = [
  '/mlsp/client/',
  '/mlsp/client/dashboard',
  '/mlsp/client/products',
  '/mlsp/client/orders',
  '/mlsp/static/client-manifest.json',
  '/mlsp/static/icons/client.png'
];

// 安装事件
self.addEventListener('install', event => {
  console.log('客户端Service Worker 安装中...');
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
  console.log('客户端Service Worker 激活中...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('milan-client-')) {
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
  const title = '米兰客户端';
  const options = {
    body: event.data ? event.data.text() : '有新消息',
    icon: '/mlsp/static/icons/client.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});
EOL

# 管理端Service Worker
cat > /home/mlsp/app/static/admin-sw.js << 'EOL'
// 管理端Service Worker
const CACHE_NAME = 'milan-admin-cache-v1';
const urlsToCache = [
  '/mlsp/admin/',
  '/mlsp/admin/dashboard',
  '/mlsp/admin/orders',
  '/mlsp/admin/products',
  '/mlsp/admin/inventory',
  '/mlsp/static/admin-manifest.json',
  '/mlsp/static/icons/admin.png'
];

// 安装事件
self.addEventListener('install', event => {
  console.log('管理端Service Worker 安装中...');
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
  console.log('管理端Service Worker 激活中...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('milan-admin-')) {
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
  const title = '米兰管理端';
  const options = {
    body: event.data ? event.data.text() : '有新订单',
    icon: '/mlsp/static/icons/admin.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
});
EOL

# 仓库端Service Worker
cat > /home/mlsp/app/static/employee-sw.js << 'EOL'
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
EOL

# 3. 创建三个不同的manifest文件
echo "创建manifest文件..."

# 客户端manifest
cat > /home/mlsp/app/static/client-manifest.json << 'EOL'
{
  "name": "米兰食品公司 - 餐馆客户端",
  "short_name": "米兰客户端",
  "description": "米兰食品公司餐馆订购系统",
  "start_url": "/mlsp/client/",
  "scope": "/mlsp/client/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#dc3545",
  "icons": [
    {
      "src": "/mlsp/static/icons/client.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
EOL

# 管理员manifest
cat > /home/mlsp/app/static/admin-manifest.json << 'EOL'
{
  "name": "米兰食品公司 - 管理后台",
  "short_name": "米兰管理端",
  "description": "米兰食品公司订单与库存管理系统",
  "start_url": "/mlsp/admin/",
  "scope": "/mlsp/admin/",
  "display": "standalone",
  "background_color": "#343a40",
  "theme_color": "#0d6efd",
  "icons": [
    {
      "src": "/mlsp/static/icons/admin.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
EOL

# 员工manifest
cat > /home/mlsp/app/static/employee-manifest.json << 'EOL'
{
  "name": "米兰食品公司 - 仓库工作台",
  "short_name": "米兰仓库端",
  "description": "米兰食品公司仓库订单处理系统",
  "start_url": "/mlsp/employee/",
  "scope": "/mlsp/employee/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#198754",
  "icons": [
    {
      "src": "/mlsp/static/icons/employee.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
EOL

# 4. 更新PWA头部，每个端口使用不同的Service Worker
echo "更新PWA头部..."

# 客户端PWA头部
cat > /home/mlsp/app/templates/client/pwa_headers.html << 'EOL'
<!-- PWA支持 -->
<link rel="manifest" href="/mlsp/static/client-manifest.json">
<meta name="theme-color" content="#dc3545">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="米兰客户端">
<link rel="apple-touch-icon" href="/mlsp/static/icons/client.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/mlsp/client/sw.js', {
      scope: '/mlsp/client/'
    }).then(function(registration) {
      console.log('客户端Service Worker 注册成功，作用域为: ', registration.scope);
    }).catch(function(error) {
      console.error('客户端Service Worker 注册失败: ', error);
    });
  });
}
</script>
EOL

# 管理员PWA头部
cat > /home/mlsp/app/templates/admin/pwa_headers.html << 'EOL'
<!-- PWA支持 -->
<link rel="manifest" href="/mlsp/static/admin-manifest.json">
<meta name="theme-color" content="#0d6efd">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="米兰管理端">
<link rel="apple-touch-icon" href="/mlsp/static/icons/admin.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/mlsp/admin/sw.js', {
      scope: '/mlsp/admin/'
    }).then(function(registration) {
      console.log('管理端Service Worker 注册成功，作用域为: ', registration.scope);
    }).catch(function(error) {
      console.error('管理端Service Worker 注册失败: ', error);
    });
  });
}
</script>
EOL

# 员工PWA头部
cat > /home/mlsp/app/templates/employee/pwa_headers.html << 'EOL'
<!-- PWA支持 -->
<link rel="manifest" href="/mlsp/static/employee-manifest.json">
<meta name="theme-color" content="#198754">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="米兰仓库端">
<link rel="apple-touch-icon" href="/mlsp/static/icons/employee.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/mlsp/employee/sw.js', {
      scope: '/mlsp/employee/'
    }).then(function(registration) {
      console.log('仓库端Service Worker 注册成功，作用域为: ', registration.scope);
    }).catch(function(error) {
      console.error('仓库端Service Worker 注册失败: ', error);
    });
  });
}
</script>
EOL

# 5. 创建PWA安装按钮脚本 - 添加到各模块
echo "创建PWA安装按钮脚本..."

# 客户端安装按钮脚本
cat > /home/mlsp/app/static/js/client-pwa-install.js << 'EOL'
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
EOL

# 复制并修改为管理端和仓库端
cp /home/mlsp/app/static/js/client-pwa-install.js /home/mlsp/app/static/js/admin-pwa-install.js
cp /home/mlsp/app/static/js/client-pwa-install.js /home/mlsp/app/static/js/employee-pwa-install.js

# 修改管理端脚本
sed -i 's/客户端/管理端/g' /home/mlsp/app/static/js/admin-pwa-install.js
sed -i 's/btn-danger/btn-primary/g' /home/mlsp/app/static/js/admin-pwa-install.js

# 修改仓库端脚本
sed -i 's/客户端/仓库端/g' /home/mlsp/app/static/js/employee-pwa-install.js
sed -i 's/btn-danger/btn-success/g' /home/mlsp/app/static/js/employee-pwa-install.js

# 6. 将安装按钮脚本添加到各自的模板
echo "将安装按钮脚本添加到模板..."

# 清除所有脚本引用
find /home/mlsp/app/templates/client -type f -name "*.html" -exec sed -i '/register-sw.js/d' {} \;
find /home/mlsp/app/templates/admin -type f -name "*.html" -exec sed -i '/register-sw.js/d' {} \;
find /home/mlsp/app/templates/employee -type f -name "*.html" -exec sed -i '/register-sw.js/d' {} \;

# 添加新脚本
find /home/mlsp/app/templates/client -type f -name "*.html" -exec sed -i '/<\/body>/i <script src="/mlsp/static/js/client-pwa-install.js"></script>' {} \;
find /home/mlsp/app/templates/admin -type f -name "*.html" -exec sed -i '/<\/body>/i <script src="/mlsp/static/js/admin-pwa-install.js"></script>' {} \;
find /home/mlsp/app/templates/employee -type f -name "*.html" -exec sed -i '/<\/body>/i <script src="/mlsp/static/js/employee-pwa-install.js"></script>' {} \;

# 7. 创建测试页面
echo "创建测试页面..."

# 客户端测试
cat > /home/mlsp/app/static/client-pwa-test.html << 'EOL'
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>客户端PWA测试</title>
  <link rel="manifest" href="/mlsp/static/client-manifest.json">
  <meta name="theme-color" content="#dc3545">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="米兰客户端">
  <link rel="apple-touch-icon" href="/mlsp/static/icons/client.png">
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
    .card { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px; }
    button { background: #dc3545; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
    a.btn { display: inline-block; text-decoration: none; padding: 10px 15px; background: #dc3545; color: white; border-radius: 5px; }
    .success { color: green; }
    .error { color: red; }
    .info { color: blue; }
  </style>
  <script>
    // 注册Service Worker
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/mlsp/client/sw.js', {
          scope: '/mlsp/client/'
        }).then(function(registration) {
          console.log('Service Worker 注册成功！', registration);
          document.getElementById('sw-status').innerHTML = 
            '<span class="success">✓ Service Worker 已注册</span><br>作用域: ' + registration.scope;
        }).catch(function(error) {
          console.error('Service Worker 注册失败:', error);
          document.getElementById('sw-status').innerHTML = 
            '<span class="error">✗ Service Worker 注册失败</span><br>' + error;
        });
      });
    }
  </script>
</head>
<body>
  <h1>米兰客户端 PWA 测试</h1>
  <img src="/mlsp/static/icons/client.png" alt="客户端图标" width="128" style="display: block; margin: 0 auto;">
  
  <div class="card">
    <h2>Service Worker</h2>
    <p id="sw-status">正在检查Service Worker...</p>
  </div>
  
  <div class="card">
    <h2>安装PWA</h2>
    <p id="install-status">正在检查安装状态...</p>
    <button id="install-btn" style="display:none;" onclick="installPWA()">安装客户端应用</button>
    
    <script>
      let deferredPrompt;
      
      window.addEventListener('beforeinstallprompt', (e) => {
        // 阻止Chrome自动显示安装提示
        e.preventDefault();
        
        // 保存事件以便稍后触发
        deferredPrompt = e;
        
        document.getElementById('install-status').innerHTML = 
          '<span class="success">✓ 此应用可以安装到主屏幕</span>';
        document.getElementById('install-btn').style.display = 'block';
      });
      
      // 检查是否已安装
      if (window.matchMedia('(display-mode: standalone)').matches || 
          window.navigator.standalone === true) {
        document.getElementById('install-status').innerHTML = 
          '<span class="info">ℹ 此应用已安装到主屏幕</span>';
      } else {
        // 延迟检查
        setTimeout(() => {
          if (document.getElementById('install-status').textContent === '正在检查安装状态...') {
            document.getElementById('install-status').innerHTML = 
              '⚠️ 未检测到安装事件。可能已安装或不满足条件';
          }
        }, 3000);
      }
      
      function installPWA() {
        if (!deferredPrompt) {
          alert('无法触发安装提示');
          return;
        }
        
        // 显示安装提示
        deferredPrompt.prompt();
        
        // 等待用户响应
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            document.getElementById('install-status').innerHTML = 
              '<span class="success">✓ 应用已成功安装</span>';
          } else {
            document.getElementById('install-status').innerHTML = 
              '<span class="error">✗ 用户拒绝安装</span>';
          }
          // 清除提示
          deferredPrompt = null;
          document.getElementById('install-btn').style.display = 'none';
        });
      }
      
      // 监听应用安装事件
      window.addEventListener('appinstalled', (evt) => {
        document.getElementById('install-status').innerHTML = 
          '<span class="success">✓ 应用已成功安装</span>';
        document.getElementById('install-btn').style.display = 'none';
      });
    </script>
  </div>
  
  <div class="card">
    <h2>访问应用</h2>
    <p><a href="/mlsp/client/" class="btn">进入客户端</a></p>
  </div>
</body>
</html>
EOL

# 管理端测试页面
cat > /home/mlsp/app/static/admin-pwa-test.html << 'EOL'
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>管理端PWA测试</title>
  <link rel="manifest" href="/mlsp/static/admin-manifest.json">
  <meta name="theme-color" content="#0d6efd">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="米兰管理端">
  <link rel="apple-touch-icon" href="/mlsp/static/icons/admin.png">
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
    .card { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px; }
    button { background: #0d6efd; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
    a.btn { display: inline-block; text-decoration: none; padding: 10px 15px; background: #0d6efd; color: white; border-radius: 5px; }
    .success { color: green; }
    .error { color: red; }
    .info { color: blue; }
  </style>
  <script>
    // 注册Service Worker
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/mlsp/admin/sw.js', {
          scope: '/mlsp/admin/'
        }).then(function(registration) {
          console.log('Service Worker 注册成功！', registration);
          document.getElementById('sw-status').innerHTML = 
            '<span class="success">✓ Service Worker 已注册</span><br>作用域: ' + registration.scope;
        }).catch(function(error) {
          console.error('Service Worker 注册失败:', error);
          document.getElementById('sw-status').innerHTML = 
            '<span class="error">✗ Service Worker 注册失败</span><br>' + error;
        });
      });
    }
  </script>
</head>
<body>
  <h1>米兰管理端 PWA 测试</h1>
  <img src="/mlsp/static/icons/admin.png" alt="管理端图标" width="128" style="display: block; margin: 0 auto;">
  
  <div class="card">
    <h2>Service Worker</h2>
    <p id="sw-status">正在检查Service Worker...</p>
  </div>
  
  <div class="card">
    <h2>安装PWA</h2>
    <p id="install-status">正在检查安装状态...</p>
    <button id="install-btn" style="display:none;" onclick="installPWA()">安装管理端应用</button>
    
    <script>
      let deferredPrompt;
      
      window.addEventListener('beforeinstallprompt', (e) => {
        // 阻止Chrome自动显示安装提示
        e.preventDefault();
        
        // 保存事件以便稍后触发
        deferredPrompt = e;
        
        document.getElementById('install-status').innerHTML = 
          '<span class="success">✓ 此应用可以安装到主屏幕</span>';
        document.getElementById('install-btn').style.display = 'block';
      });
      
      // 检查是否已安装
      if (window.matchMedia('(display-mode: standalone)').matches || 
          window.navigator.standalone === true) {
        document.getElementById('install-status').innerHTML = 
          '<span class="info">ℹ 此应用已安装到主屏幕</span>';
      } else {
        // 延迟检查
        setTimeout(() => {
          if (document.getElementById('install-status').textContent === '正在检查安装状态...') {
            document.getElementById('install-status').innerHTML = 
              '⚠️ 未检测到安装事件。可能已安装或不满足条件';
          }
        }, 3000);
      }
      
      function installPWA() {
        if (!deferredPrompt) {
          alert('无法触发安装提示');
          return;
        }
        
        // 显示安装提示
        deferredPrompt.prompt();
        
        // 等待用户响应
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            document.getElementById('install-status').innerHTML = 
              '<span class="success">✓ 应用已成功安装</span>';
          } else {
            document.getElementById('install-status').innerHTML = 
              '<span class="error">✗ 用户拒绝安装</span>';
          }
          // 清除提示
          deferredPrompt = null;
          document.getElementById('install-btn').style.display = 'none';
        });
      }
      
      // 监听应用安装事件
      window.addEventListener('appinstalled', (evt) => {
        document.getElementById('install-status').innerHTML = 
          '<span class="success">✓ 应用已成功安装</span>';
        document.getElementById('install-btn').style.display = 'none';
      });
    </script>
  </div>
  
  <div class="card">
    <h2>访问应用</h2>
    <p><a href="/mlsp/admin/" class="btn">进入管理端</a></p>
  </div>
</body>
</html>
EOL

# 仓库端测试页面
cat > /home/mlsp/app/static/employee-pwa-test.html << 'EOL'
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>仓库端PWA测试</title>
  <link rel="manifest" href="/mlsp/static/employee-manifest.json">
  <meta name="theme-color" content="#198754">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="米兰仓库端">
  <link rel="apple-touch-icon" href="/mlsp/static/icons/employee.png">
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
    .card { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px; }
    button { background: #198754; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
    a.btn { display: inline-block; text-decoration: none; padding: 10px 15px; background: #198754; color: white; border-radius: 5px; }
    .success { color: green; }
    .error { color: red; }
    .info { color: blue; }
  </style>
  <script>
    // 注册Service Worker
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/mlsp/employee/sw.js', {
          scope: '/mlsp/employee/'
        }).then(function(registration) {
          console.log('Service Worker 注册成功！', registration);
          document.getElementById('sw-status').innerHTML = 
            '<span class="success">✓ Service Worker 已注册</span><br>作用域: ' + registration.scope;
        }).catch(function(error) {
          console.error('Service Worker 注册失败:', error);
          document.getElementById('sw-status').innerHTML = 
            '<span class="error">✗ Service Worker 注册失败</span><br>' + error;
        });
      });
    }
  </script>
</head>
<body>
  <h1>米兰仓库端 PWA 测试</h1>
  <img src="/mlsp/static/icons/employee.png" alt="仓库端图标" width="128" style="display: block; margin: 0 auto;">
  
  <div class="card">
    <h2>Service Worker</h2>
    <p id="sw-status">正在检查Service Worker...</p>
  </div>
  
  <div class="card">
    <h2>安装PWA</h2>
    <p id="install-status">正在检查安装状态...</p>
    <button id="install-btn" style="display:none;" onclick="installPWA()">安装仓库端应用</button>
    
    <script>
      let deferredPrompt;
      
      window.addEventListener('beforeinstallprompt', (e) => {
        // 阻止Chrome自动显示安装提示
        e.preventDefault();
        
        // 保存事件以便稍后触发
        deferredPrompt = e;
        
        document.getElementById('install-status').innerHTML = 
          '<span class="success">✓ 此应用可以安装到主屏幕</span>';
        document.getElementById('install-btn').style.display = 'block';
      });
      
      // 检查是否已安装
      if (window.matchMedia('(display-mode: standalone)').matches || 
          window.navigator.standalone === true) {
        document.getElementById('install-status').innerHTML = 
          '<span class="info">ℹ 此应用已安装到主屏幕</span>';
      } else {
        // 延迟检查
        setTimeout(() => {
          if (document.getElementById('install-status').textContent === '正在检查安装状态...') {
            document.getElementById('install-status').innerHTML = 
              '⚠️ 未检测到安装事件。可能已安装或不满足条件';
          }
        }, 3000);
      }
      
      function installPWA() {
        if (!deferredPrompt) {
          alert('无法触发安装提示');
          return;
        }
        
        // 显示安装提示
        deferredPrompt.prompt();
        
        // 等待用户响应
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            document.getElementById('install-status').innerHTML = 
              '<span class="success">✓ 应用已成功安装</span>';
          } else {
            document.getElementById('install-status').innerHTML = 
              '<span class="error">✗ 用户拒绝安装</span>';
          }
          // 清除提示
          deferredPrompt = null;
          document.getElementById('install-btn').style.display = 'none';
        });
      }
      
      // 监听应用安装事件
      window.addEventListener('appinstalled', (evt) => {
        document.getElementById('install-status').innerHTML = 
          '<span class="success">✓ 应用已成功安装</span>';
        document.getElementById('install-btn').style.display = 'none';
      });
    </script>
  </div>
  
  <div class="card">
    <h2>访问应用</h2>
    <p><a href="/mlsp/employee/" class="btn">进入仓库端</a></p>
  </div>
</body>
</html>
EOL

# 创建入口页
cat > /home/mlsp/app/static/pwa-selector.html << 'EOL'
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>米兰食品公司 PWA 测试</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f5f5f5; }
    h1 { text-align: center; margin-bottom: 30px; color: #333; }
    h2 { color: #444; }
    .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .app-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
    .app-card { background: white; border-radius: 10px; padding: 20px; text-align: center; transition: transform 0.3s; }
    .app-card:hover { transform: translateY(-5px); }
    .app-icon { width: 100px; height: 100px; margin: 0 auto 15px; display: block; }
    .app-button { display: inline-block; text-decoration: none; padding: 10px 20px; border-radius: 5px; color: white; font-weight: bold; margin-top: 15px; }
    .client { background-color: #dc3545; }
    .admin { background-color: #0d6efd; }
    .employee { background-color: #198754; }
    .instructions { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0d6efd; margin: 20px 0; }
  </style>
</head>
<body>
  <h1>米兰食品公司 PWA 应用</h1>
  
  <div class="card">
    <h2>选择您要使用的应用</h2>
    <p>米兰食品公司系统有三个独立的应用，每个都可以安装到您的主屏幕。请选择您需要的应用：</p>
    
    <div class="app-grid">
      <div class="app-card">
        <img src="/mlsp/static/icons/client.png" alt="客户端" class="app-icon">
        <h3>客户端</h3>
        <p>适合餐馆用户下单使用</p>
        <a href="/mlsp/static/client-pwa-test.html" class="app-button client">进入客户端</a>
      </div>
      
      <div class="app-card">
        <img src="/mlsp/static/icons/admin.png" alt="管理端" class="app-icon">
        <h3>管理端</h3>
        <p>适合管理员使用</p>
        <a href="/mlsp/static/admin-pwa-test.html" class="app-button admin">进入管理端</a>
      </div>
      
      <div class="app-card">
        <img src="/mlsp/static/icons/employee.png" alt="仓库端" class="app-icon">
        <h3>仓库端</h3>
        <p>适合仓库员工使用</p>
        <a href="/mlsp/static/employee-pwa-test.html" class="app-button employee">进入仓库端</a>
      </div>
    </div>
  </div>
  
  <div class="card">
    <h2>安装指南</h2>
    <div class="instructions">
      <p><strong>如何安装PWA应用：</strong></p>
      <ol>
        <li>点击上方相应的应用入口</li>
        <li>在打开的测试页面中，点击"安装XX应用"按钮</li>
        <li>根据浏览器提示完成安装</li>
      </ol>
      <p><strong>注意：</strong> 如果您之前已经安装过任何一个应用，可能需要先清除浏览器缓存和Service Worker，然后重新尝试。</p>
    </div>
  </div>
</body>
</html>
EOL

# 8. 重启应用
echo "重启应用..."
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "三个独立的PWA配置已完成！"
echo "请访问 https://ritmohub.cn/mlsp/static/pwa-selector.html 选择要安装的应用"
echo "每个应用有独立的图标、颜色和名称，可以分别安装到主屏幕"
