#!/bin/bash

# 创建输出目录
mkdir -p /home/mlsp/app/static/icons

# 客户端图标 - 红色
convert -size 192x192 xc:'#dc3545' -fill white -gravity center -pointsize 48 -annotate 0 "客户端" /home/mlsp/app/static/icons/client-192.png
convert -size 512x512 xc:'#dc3545' -fill white -gravity center -pointsize 128 -annotate 0 "客户端" /home/mlsp/app/static/icons/client-512.png

# 管理端图标 - 蓝色
convert -size 192x192 xc:'#0d6efd' -fill white -gravity center -pointsize 48 -annotate 0 "管理端" /home/mlsp/app/static/icons/admin-192.png
convert -size 512x512 xc:'#0d6efd' -fill white -gravity center -pointsize 128 -annotate 0 "管理端" /home/mlsp/app/static/icons/admin-512.png

# 员工端图标 - 绿色
convert -size 192x192 xc:'#198754' -fill white -gravity center -pointsize 48 -annotate 0 "员工端" /home/mlsp/app/static/icons/employee-192.png
convert -size 512x512 xc:'#198754' -fill white -gravity center -pointsize 128 -annotate 0 "员工端" /home/mlsp/app/static/icons/employee-512.png

echo "图标创建完成"
