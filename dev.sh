#!/bin/bash

# 停止已存在的进程
if [ -f /home/mlsp/app.pid ]; then
    pid=$(cat /home/mlsp/app.pid)
    echo "停止现有进程 $pid"
    kill $pid 2>/dev/null
    rm /home/mlsp/app.pid
fi

# 确保目录存在
mkdir -p /home/mlsp/app/static/qrcodes/shelves
mkdir -p /home/mlsp/app/static/qrcodes/slots
mkdir -p /home/mlsp/app/static/uploads/order_photos
mkdir -p /home/mlsp/app/static/uploads/products
chmod -R 777 /home/mlsp/app/static

# 使用 uvicorn 的自动重载功能直接启动
echo "启动开发模式（自动重载）..."
cd /home/mlsp
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --root-path /mlsp --reload > app.log 2>&1 &
echo $! > app.pid
echo "开发模式已启动（进程ID: $(cat app.pid)）"
echo "日志文件: /home/mlsp/app.log"
echo "使用 bash /home/mlsp/stop.sh 停止应用"
