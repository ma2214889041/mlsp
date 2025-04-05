#!/bin/bash

# 删除旧的Service Worker注册
echo "正在查找并移除旧的Service Worker注册..."
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/serviceWorker\.register/d' {} \;

# 添加新的Service Worker注册代码到所有HTML文件
echo "添加新的Service Worker注册代码..."
cat > /home/mlsp/app/static/js/sw-register.js << EOFJS
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/mlsp/static/sw.js', {
      scope: '/mlsp/'
    }).then(function(registration) {
      console.log('Service Worker 注册成功，作用域为: ', registration.scope);
    }).catch(function(error) {
      console.log('Service Worker 注册失败: ', error);
    });
  });
}
EOFJS

# 添加新的Service Worker注册脚本到所有HTML文件
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/<\/head>/i <script src="/mlsp/static/js/sw-register.js"></script>' {} \;

# 复制PWA检查页面到静态目录
cp /home/mlsp/app/static/pwa-check.html /home/mlsp/app/static/

# 重新启动应用
echo "重启应用..."
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "修复完成! 请访问 https://ritmohub.cn/mlsp/static/pwa-check.html 检查PWA状态"
