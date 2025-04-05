#!/bin/bash

# 添加PWA指南脚本到所有HTML文件
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已包含PWA指南脚本
    if ! grep -q "pwa-guide.js" "$file"; then
      # 在body结束标签前插入脚本
      sed -i '/<\/body>/i <script src="/static/js/pwa-guide.js"></script>' "$file"
      echo "已添加PWA指南脚本到 $file"
    else
      echo "$file 已包含PWA指南脚本"
    fi
    
    # 移除旧的manifest链接（如果存在）
    # 这一步是为了让我们的动态脚本能够添加正确的manifest
    if grep -q "manifest" "$file"; then
      sed -i '/rel="manifest"/d' "$file"
      echo "已移除旧的manifest链接从 $file"
    fi
    
    # 确保viewport设置正确
    if ! grep -q "viewport" "$file" || ! grep -q "user-scalable=no" "$file"; then
      # 如果已有viewport标签，则替换它
      if grep -q "viewport" "$file"; then
        sed -i 's|<meta name="viewport".*>|<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">|' "$file"
      else
        # 否则添加新的viewport标签
        sed -i '/<head>/a <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">' "$file"
      fi
      echo "已更新viewport设置在 $file"
    fi
    
    # 添加基本的PWA标签
    if ! grep -q "apple-mobile-web-app-capable" "$file"; then
      sed -i '/<head>/a <meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-status-bar-style" content="black">' "$file"
      echo "已添加基本PWA标签到 $file"
    fi
  done
done

echo "所有HTML文件已更新PWA设置"
