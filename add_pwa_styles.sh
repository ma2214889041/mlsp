#!/bin/bash

# 添加PWA样式到所有HTML文件
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已包含PWA样式
    if ! grep -q "pwa-styles.css" "$file"; then
      # 在head结束标签前插入样式链接
      sed -i '/<\/head>/i <link rel="stylesheet" href="/static/css/pwa-styles.css">' "$file"
      echo "已添加PWA样式到 $file"
    else
      echo "$file 已包含PWA样式"
    fi
  done
done

echo "所有HTML文件已添加PWA样式"
