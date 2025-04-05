#!/bin/bash

# 在所有客户端模板中添加PWA头部
for file in /home/mlsp/app/templates/client/*.html; do
  if ! grep -q "PWA支持" "$file"; then
    sed -i '/<head>/r /home/mlsp/app/templates/client/pwa_headers.html' "$file"
    echo "已添加PWA支持到 $file"
  else
    echo "文件 $file 已经包含PWA支持"
  fi
done

# 在所有管理员模板中添加PWA头部
for file in /home/mlsp/app/templates/admin/*.html; do
  if ! grep -q "PWA支持" "$file"; then
    sed -i '/<head>/r /home/mlsp/app/templates/admin/pwa_headers.html' "$file"
    echo "已添加PWA支持到 $file"
  else
    echo "文件 $file 已经包含PWA支持"
  fi
done

# 在所有员工模板中添加PWA头部
for file in /home/mlsp/app/templates/employee/*.html; do
  if ! grep -q "PWA支持" "$file"; then
    sed -i '/<head>/r /home/mlsp/app/templates/employee/pwa_headers.html' "$file"
    echo "已添加PWA支持到 $file"
  else
    echo "文件 $file 已经包含PWA支持"
  fi
done

echo "PWA头部添加完成！"
