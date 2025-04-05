#!/bin/bash

echo "开始修复PWA功能..."

# 1. 先确保所有必要的目录存在
mkdir -p /home/mlsp/app/static/icons
mkdir -p /home/mlsp/app/static/js

# 2. 创建三个不同的图标（如果没有ImageMagick，请手动上传图标）
if command -v convert &> /dev/null; then
    # 客户端图标 - 红色
    convert -size 192x192 xc:white -fill red -gravity center -pointsize 40 -annotate 0 "客户端" /home/mlsp/app/static/icons/client.png
    # 管理端图标 - 蓝色
    convert -size 192x192 xc:white -fill blue -gravity center -pointsize 40 -annotate 0 "管理端" /home/mlsp/app/static/icons/admin.png
    # 员工端图标 - 绿色
    convert -size 192x192 xc:white -fill green -gravity center -pointsize 40 -annotate 0 "仓库端" /home/mlsp/app/static/icons/employee.png
    echo "已创建示例图标"
else
    echo "未找到ImageMagick，请手动准备图标文件"
    # 创建空文件作为占位符
    touch /home/mlsp/app/static/icons/client.png
    touch /home/mlsp/app/static/icons/admin.png
    touch /home/mlsp/app/static/icons/employee.png
fi

# 3. 创建manifest文件
echo "创建manifest文件..."

# 客户端manifest
cat > /home/mlsp/app/static/client-manifest.json << 'EOL'
{
  "name": "米兰食品公司 - The Milan Food Company",
  "short_name": "米兰客户端",
  "description": "米兰食品公司餐馆订购系统",
  "start_url": "/mlsp/client/",
  "scope": "/mlsp/",
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
  "scope": "/mlsp/",
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
  "scope": "/mlsp/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0d6efd",
  "icons": [
    {
      "src": "/mlsp/static/icons/employee.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
EOL

# 4. 创建Service Worker文件
echo "创建Service Worker文件..."

cat > /home/mlsp/app/static/sw.js << 'EOL'
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
EOL

# 5. 创建Service Worker注册脚本
cat > /home/mlsp/app/static/js/register-sw.js << 'EOL'
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
EOL

# 6. 更新PWA头部
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
EOL

# 员工PWA头部
cat > /home/mlsp/app/templates/employee/pwa_headers.html << 'EOL'
<!-- PWA支持 -->
<link rel="manifest" href="/mlsp/static/employee-manifest.json">
<meta name="theme-color" content="#0d6efd">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="米兰仓库端">
<link rel="apple-touch-icon" href="/mlsp/static/icons/employee.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
EOL

# 7. 更新所有HTML文件，添加PWA头部和Service Worker注册
echo "更新HTML文件..."

# 移除所有页面中旧的Service Worker注册
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/serviceWorker\.register/d' {} \;

# 应用PWA头部
bash /home/mlsp/update_pwa_headers.sh

# 添加Service Worker注册到所有HTML文件
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/<\/body>/i <script src="/mlsp/static/js/register-sw.js"></script>' {} \;

# 8. 创建PWA测试页面
echo "创建PWA测试页面..."

cat > /home/mlsp/app/static/pwa-test.html << 'EOL'
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PWA测试</title>
  <link rel="manifest" href="/mlsp/static/client-manifest.json">
  <meta name="theme-color" content="#dc3545">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
    .card { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px; }
    button { background: #0d6efd; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
    .btn-group { margin: 20px 0; }
    .btn-group a { display: inline-block; text-decoration: none; padding: 10px 15px; margin-right: 10px; 
                  color: white; border-radius: 5px; }
    .client { background-color: #dc3545; }
    .admin { background-color: #0d6efd; }
    .employee { background-color: #198754; }
    .success { color: green; }
    .error { color: red; }
    .info { color: blue; }
  </style>
</head>
<body>
  <h1>米兰食品公司 PWA 测试</h1>
  
  <div class="card">
    <h2>Service Worker</h2>
    <p id="sw-status">正在检查...</p>
    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/mlsp/static/sw.js')
          .then(reg => {
            document.getElementById('sw-status').innerHTML = 
              '<span class="success">✓ Service Worker已注册</span><br>作用域: ' + reg.scope;
          })
          .catch(err => {
            document.getElementById('sw-status').innerHTML = 
              '<span class="error">✗ Service Worker注册失败</span><br>' + err;
          });
      } else {
        document.getElementById('sw-status').innerHTML = 
          '<span class="error">✗ 浏览器不支持Service Worker</span>';
      }
    </script>
  </div>
  
  <div class="card">
    <h2>安装PWA</h2>
    <p id="install-status">检查中...</p>
    <button id="install-btn" style="display:none;" onclick="installPWA()">安装应用</button>
    
    <script>
      let deferredPrompt;
      
      window.addEventListener('beforeinstallprompt', (e) => {
        // 阻止自动显示安装提示
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
      }
      
      // 5秒后检查
      setTimeout(() => {
        if (document.getElementById('install-status').innerHTML === '检查中...') {
          document.getElementById('install-status').innerHTML = 
            '⚠️ 未检测到安装事件。可能原因：<br>- 已安装<br>- 已拒绝安装<br>- 浏览器不支持<br>- 不满足安装条件';
        }
      }, 5000);
      
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
          // 清除提示，它只能使用一次
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
    <div class="btn-group">
      <a href="/mlsp/client/" class="client">客户端</a>
      <a href="/mlsp/admin/" class="admin">管理端</a>
      <a href="/mlsp/employee/" class="employee">仓库端</a>
    </div>
  </div>
  
  <div class="card">
    <h2>清除Service Worker</h2>
    <p>如果遇到问题，可以尝试清除当前注册的Service Worker：</p>
    <button onclick="clearServiceWorker()">清除Service Worker</button>
    <p id="clear-result"></p>
    
    <script>
      function clearServiceWorker() {
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.getRegistrations().then(registrations => {
            const promises = registrations.map(registration => registration.unregister());
            Promise.all(promises).then(() => {
              document.getElementById('clear-result').innerHTML = 
                '<span class="success">已清除所有Service Worker</span><br>请刷新页面重新注册';
            });
          });
        }
      }
    </script>
  </div>
</body>
</html>
EOL

# 9. 重启应用
echo "重启应用..."
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "PWA修复完成!"
echo "请访问 https://ritmohub.cn/mlsp/static/pwa-test.html 测试PWA功能"
echo "如果仍然有问题，请确保以下几点："
echo "1. 清除浏览器缓存和Service Worker"
echo "2. 确保使用HTTPS访问"
echo "3. 使用Chrome或Safari尝试"
