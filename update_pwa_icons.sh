#!/bin/bash

# 更新客户端页面
for file in /home/mlsp/app/templates/client/*.html; do
  # 移除旧的PWA头部（如果存在）
  if grep -q "apple-mobile-web-app-capable" "$file"; then
    # 找到<head>标签开始和第一个apple-mobile-web-app相关标签之间的行号
    START_LINE=$(grep -n "<head>" "$file" | cut -d: -f1)
    END_LINE=$(grep -n "apple-mobile-web-app" "$file" | head -n 1 | cut -d: -f1)
    
    # 计算需要删除的行数
    if [ -n "$START_LINE" ] && [ -n "$END_LINE" ]; then
      # 确保END_LINE大于START_LINE
      if [ $END_LINE -gt $START_LINE ]; then
        # 删除旧的PWA标签
        PWA_LINES=$(grep -n "apple-mobile-web\|manifest\|theme-color\|apple-touch-icon\|viewport" "$file" | cut -d: -f1)
        for line in $PWA_LINES; do
          sed -i "${line}d" "$file"
        done
      fi
    fi
  fi
  
  # 添加新的PWA头部
  sed -i '/<head>/r /home/mlsp/app/templates/client/pwa_headers.html' "$file"
  echo "已更新 $file 的PWA头部"
done

# 更新管理员页面
for file in /home/mlsp/app/templates/admin/*.html; do
  # 移除旧的PWA头部（如果存在）
  if grep -q "apple-mobile-web-app-capable" "$file"; then
    # 删除包含指定关键词的行
    sed -i '/apple-mobile-web\|manifest\|theme-color\|apple-touch-icon\|viewport/d' "$file"
  fi
  
  # 添加新的PWA头部
  sed -i '/<head>/r /home/mlsp/app/templates/admin/pwa_headers.html' "$file"
  echo "已更新 $file 的PWA头部"
done

# 更新员工页面
for file in /home/mlsp/app/templates/employee/*.html; do
  # 移除旧的PWA头部（如果存在）
  if grep -q "apple-mobile-web-app-capable" "$file"; then
    # 删除包含指定关键词的行
    sed -i '/apple-mobile-web\|manifest\|theme-color\|apple-touch-icon\|viewport/d' "$file"
  fi
  
  # 添加新的PWA头部
  sed -i '/<head>/r /home/mlsp/app/templates/employee/pwa_headers.html' "$file"
  echo "已更新 $file 的PWA头部"
done

echo "所有HTML文件的PWA头部已更新完成！"
