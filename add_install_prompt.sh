#!/bin/bash

# 添加PWA安装提示脚本到所有模板
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    if ! grep -q "pwa-install.js" "$file"; then
      sed -i '/<\/body>/i <script src="/static/js/pwa-install.js"></script>' "$file"
      echo "已添加安装提示到 $file"
    else
      echo "文件 $file 已包含安装提示"
    fi
  done
done

echo "安装提示添加完成！"
