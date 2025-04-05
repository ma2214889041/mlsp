#!/bin/bash

# 更新所有HTML模板，使用最小PWA脚本
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 替换原来的PWA安装脚本
    if grep -q "pwa-install.js" "$file"; then
      sed -i 's|/static/js/pwa-install.js|/static/js/pwa-install-minimal.js|g' "$file"
      echo "已更新 $file 的PWA安装脚本"
    else
      # 添加PWA安装脚本
      sed -i '/<\/body>/i <script src="/static/js/pwa-install-minimal.js"></script>' "$file"
      echo "已添加PWA安装脚本到 $file"
    fi
    
    # 更新Viewport设置
    if ! grep -q "viewport-fit=cover" "$file"; then
      sed -i 's|<meta name="viewport" content="width=device-width, initial-scale=1.0">|<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">|g' "$file"
      echo "已更新 $file 的viewport设置"
    fi
  done
done

echo "所有模板PWA脚本更新完成！"
