#!/bin/bash

# 将重要的Service Worker文件复制到根目录
echo "正在复制Service Worker文件到合适的位置..."
cp /home/mlsp/app/static/sw.js /home/mlsp/app/sw.js

# 修改FastAPI应用添加根路径的Service Worker路由
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

# 根目录Service Worker路由
@app.get("/sw.js")
async def get_service_worker():
    return FileResponse("/home/mlsp/app/sw.js")

# 各模块Service Worker路由
@app.get("/client-sw.js")
async def get_client_sw():
    return FileResponse("/home/mlsp/app/static/client-sw.js")

@app.get("/admin-sw.js")
async def get_admin_sw():
    return FileResponse("/home/mlsp/app/static/admin-sw.js")

@app.get("/employee-sw.js")
async def get_employee_sw():
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

# 创建通用的Service Worker文件
cat > /home/mlsp/app/sw.js << 'EOL'
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
EOL

# 为每个端创建特定的Service Worker
cp /home/mlsp/app/sw.js /home/mlsp/app/static/client-sw.js
cp /home/mlsp/app/sw.js /home/mlsp/app/static/admin-sw.js
cp /home/mlsp/app/sw.js /home/mlsp/app/static/employee-sw.js

# 更新PWA头部
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
    navigator.serviceWorker.register('/mlsp/sw.js', {
      scope: '/mlsp/'
    }).then(function(registration) {
      console.log('Service Worker 注册成功，作用域为: ', registration.scope);
    }).catch(function(error) {
      console.error('Service Worker 注册失败: ', error);
    });
  });
}
</script>
EOL

# 创建特定端PWA安装测试页面
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
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; text-align: center; }
    .btn { display: inline-block; padding: 10px 20px; background-color: #dc3545; color: white;
           border-radius: 5px; text-decoration: none; margin: 20px 0; }
  </style>
  <script>
    // 注册Service Worker
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/mlsp/sw.js', {
          scope: '/mlsp/'
        }).then(function(registration) {
          console.log('Service Worker 注册成功！', registration);
          document.getElementById('sw-status').textContent = '✅ Service Worker 已注册';
        }).catch(function(error) {
          console.error('Service Worker 注册失败:', error);
          document.getElementById('sw-status').textContent = '❌ Service Worker 注册失败: ' + error;
        });
      });
    }
    
    // 处理安装事件
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
      // 阻止Chrome 67+自动显示安装提示
      e.preventDefault();
      // 保存事件以便稍后触发
      deferredPrompt = e;
      
      document.getElementById('install-btn').style.display = 'block';
      document.getElementById('install-status').textContent = '✅ 此应用可安装至主屏幕';
    });
    
    function installApp() {
      if (!deferredPrompt) {
        alert('无法安装应用。可能已安装或浏览器不支持。');
        return;
      }
      
      // 显示安装提示
      deferredPrompt.prompt();
      
      // 等待用户响应
      deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('用户接受安装');
          document.getElementById('install-status').textContent = '✅ 应用安装成功！';
        } else {
          console.log('用户拒绝安装');
          document.getElementById('install-status').textContent = '❌ 用户拒绝安装';
        }
        // 清除提示，因为它只能使用一次
        deferredPrompt = null;
        document.getElementById('install-btn').style.display = 'none';
      });
    }
    
    // 检测是否已安装
    window.addEventListener('appinstalled', (evt) => {
      document.getElementById('install-status').textContent = '✅ 应用已成功安装！';
      document.getElementById('install-btn').style.display = 'none';
    });
  </script>
</head>
<body>
  <h1>米兰客户端 PWA 测试</h1>
  <img src="/mlsp/static/icons/client.png" alt="客户端图标" width="128">
  
  <p id="sw-status">正在检查Service Worker...</p>
  <p id="install-status">等待安装检测...</p>
  
  <button id="install-btn" onclick="installApp()" style="display:none;">安装客户端到主屏幕</button>
  
  <p>
    <a href="/mlsp/client/" class="btn">进入客户端</a>
  </p>
  
  <script>
    // 5秒后检查安装状态
    setTimeout(() => {
      if (document.getElementById('install-status').textContent === '等待安装检测...') {
        if (window.matchMedia('(display-mode: standalone)').matches || 
            window.navigator.standalone === true) {
          document.getElementById('install-status').textContent = '✅ 应用已安装并在运行';
        } else {
          document.getElementById('install-status').textContent = '⚠️ 未收到安装事件。可能已安装或不满足条件';
        }
      }
    }, 5000);
  </script>
</body>
</html>
EOL

# 复制测试页面到管理端和员工端
cp /home/mlsp/app/static/client-pwa-test.html /home/mlsp/app/static/admin-pwa-test.html
cp /home/mlsp/app/static/client-pwa-test.html /home/mlsp/app/static/employee-pwa-test.html

# 自定义管理端测试页面
sed -i 's/客户端PWA测试/管理端PWA测试/g' /home/mlsp/app/static/admin-pwa-test.html
sed -i 's/client-manifest.json/admin-manifest.json/g' /home/mlsp/app/static/admin-pwa-test.html
sed -i 's/米兰客户端/米兰管理端/g' /home/mlsp/app/static/admin-pwa-test.html
sed -i 's/client.png/admin.png/g' /home/mlsp/app/static/admin-pwa-test.html
sed -i 's/#dc3545/#0d6efd/g' /home/mlsp/app/static/admin-pwa-test.html
sed -i 's/客户端到主屏幕/管理端到主屏幕/g' /home/mlsp/app/static/admin-pwa-test.html
sed -i 's|/mlsp/client/|/mlsp/admin/|g' /home/mlsp/app/static/admin-pwa-test.html

# 自定义员工端测试页面
sed -i 's/客户端PWA测试/仓库端PWA测试/g' /home/mlsp/app/static/employee-pwa-test.html
sed -i 's/client-manifest.json/employee-manifest.json/g' /home/mlsp/app/static/employee-pwa-test.html
sed -i 's/米兰客户端/米兰仓库端/g' /home/mlsp/app/static/employee-pwa-test.html
sed -i 's/client.png/employee.png/g' /home/mlsp/app/static/employee-pwa-test.html
sed -i 's/#dc3545/#198754/g' /home/mlsp/app/static/employee-pwa-test.html
sed -i 's/客户端到主屏幕/仓库端到主屏幕/g' /home/mlsp/app/static/employee-pwa-test.html
sed -i 's|/mlsp/client/|/mlsp/employee/|g' /home/mlsp/app/static/employee-pwa-test.html

# 运行更新PWA头部和重启应用程序
bash /home/mlsp/update_pwa_headers.sh
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "PWA修复完成!请访问以下测试页面:"
echo "- 客户端: https://ritmohub.cn/mlsp/static/client-pwa-test.html"
echo "- 管理端: https://ritmohub.cn/mlsp/static/admin-pwa-test.html"
echo "- 仓库端: https://ritmohub.cn/mlsp/static/employee-pwa-test.html"
