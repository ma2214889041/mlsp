#!/bin/bash

# 添加Service Worker注册代码到所有HTML文件
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已包含Service Worker注册代码
    if ! grep -q "register-sw.js" "$file"; then
      # 在body结束标签前插入脚本
      sed -i '/<\/body>/i <script src="/static/js/register-sw.js"></script>' "$file"
      echo "已添加Service Worker注册代码到 $file"
    else
      echo "$file 已包含Service Worker注册代码"
    fi
  done
done

echo "所有HTML文件已添加Service Worker注册代码"
