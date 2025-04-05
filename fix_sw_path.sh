#!/bin/bash

# 准备Service Worker相关文件
cp /home/mlsp/app/static/sw.js /home/mlsp/sw.js
cp /home/mlsp/app/static/root-sw.js /home/mlsp/sw.js
cp /home/mlsp/app/static/pwa-test-root.html /home/mlsp/app/static/

# 修改所有HTML文件中的Service Worker注册
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/serviceWorker\.register/d' {} \;

# 添加新的注册脚本
cat > /home/mlsp/app/static/js/sw-register.js << EOFJS
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/mlsp/sw.js')
      .then(function(registration) {
        console.log('Service Worker 注册成功，作用域为: ', registration.scope);
      })
      .catch(function(error) {
        console.log('Service Worker 注册失败: ', error);
      });
  });
}
EOFJS

# 添加新的Service Worker注册脚本到所有HTML文件
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/<\/head>/i <script src="/mlsp/static/js/sw-register.js"></script>' {} \;

# 重启应用
echo "正在重启应用..."
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "修复完成! 请访问 https://ritmohub.cn/mlsp/static/pwa-test-root.html 测试Service Worker"
