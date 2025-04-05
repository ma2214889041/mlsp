#!/bin/bash

# 将PWA模式脚本添加到所有模板
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已经包含脚本
    if ! grep -q "pwa-mode.js" "$file"; then
      # 在</body>标签前插入脚本
      sed -i '/<\/body>/i <script src="/static/js/pwa-mode.js"></script>' "$file"
      echo "已添加PWA模式脚本到 $file"
    else
      echo "文件 $file 已包含PWA模式脚本"
    fi
  done
done

echo "所有模板PWA模式脚本添加完成！"
