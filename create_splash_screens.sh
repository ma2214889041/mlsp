#!/bin/bash

# 客户端启动屏幕
echo "创建客户端启动屏幕"
cat > /home/mlsp/app/static/icons/client-splash.png << 'IMAGE'
(这里应插入实际的二进制图像数据)
IMAGE

# 管理端启动屏幕
echo "创建管理端启动屏幕"
cat > /home/mlsp/app/static/icons/admin-splash.png << 'IMAGE'
(这里应插入实际的二进制图像数据)
IMAGE

# 员工端启动屏幕
echo "创建员工端启动屏幕"
cat > /home/mlsp/app/static/icons/employee-splash.png << 'IMAGE'
(这里应插入实际的二进制图像数据)
IMAGE

echo "启动屏幕创建完成！"
