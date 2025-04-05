#!/bin/bash

# 更新所有HTML模板的PWA头部
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已经包含PWA头部
    if ! grep -q "apple-mobile-web-app-capable" "$file"; then
      # 在<head>标签后插入PWA头部内容
      sed -i '/<head>/r /home/mlsp/app/templates/'$dir'/pwa_headers.html' "$file"
      echo "已更新 $file 的PWA头部"
    else
      echo "文件 $file 已包含PWA头部"
    fi
  done
done

echo "所有模板PWA头部更新完成！"
