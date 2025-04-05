#!/bin/bash

# 添加基本PWA支持到所有HTML文件
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已包含PWA支持
    if ! grep -q "apple-mobile-web-app-capable" "$file"; then
      # 在head标签后插入PWA基本支持
      sed -i '/<head>/r /home/mlsp/app/templates/pwa_basic.html' "$file"
      echo "已添加PWA基本支持到 $file"
    else
      echo "$file 已包含PWA支持"
    fi
  done
done

echo "所有HTML文件已添加PWA基本支持"
