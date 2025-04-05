#!/bin/bash

# 在生产环境中，您应该使用真实的PNG图标文件代替这些占位符

# 客户端图标 - 红色
convert -size 192x192 xc:white -fill red -gravity center -pointsize 40 -annotate 0 "客户端" /home/mlsp/app/static/icons/client.png

# 管理端图标 - 蓝色
convert -size 192x192 xc:white -fill blue -gravity center -pointsize 40 -annotate 0 "管理端" /home/mlsp/app/static/icons/admin.png

# 员工端图标 - 绿色
convert -size 192x192 xc:white -fill green -gravity center -pointsize 40 -annotate 0 "仓库端" /home/mlsp/app/static/icons/employee.png

echo "已创建不同的图标文件"
