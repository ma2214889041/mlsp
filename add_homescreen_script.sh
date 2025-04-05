#!/bin/bash

# 添加添加到主屏幕脚本到所有HTML文件
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已包含脚本
    if ! grep -q "add-to-homescreen.js" "$file"; then
      # 在body结束标签前插入脚本
      sed -i '/<\/body>/i <script src="/static/js/add-to-homescreen.js"></script>' "$file"
      echo "已添加添加到主屏幕脚本到 $file"
    else
      echo "$file 已包含添加到主屏幕脚本"
    fi
  done
done

echo "所有HTML文件已添加添加到主屏幕脚本"
