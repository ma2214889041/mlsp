#!/bin/bash

# 移除所有页面中的旧Service Worker注册
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/serviceWorker\.register/d' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i '/<script src="\/mlsp\/static\/js\/sw-register.js"><\/script>/d' {} \;

# 更新页面头部
bash /home/mlsp/update_pwa_headers.sh

# 重启应用
echo "正在重启应用..."
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "修复完成! 各端口现在应该有不同的PWA图标和配置了。"
