#!/bin/bash

# 运行安装脚本确保依赖已安装
./install_deps.sh

# 停止现有进程
if [ -f /home/mlsp/app.pid ]; then
    pid=$(cat /home/mlsp/app.pid)
    echo "停止已运行的进程 $pid"
    kill $pid 2>/dev/null || true
    rm /home/mlsp/app.pid
fi

# 启动应用
echo "启动应用..."
cd /home/mlsp
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
echo $! > app.pid
echo "应用已在后台启动，进程ID保存在app.pid"
echo "使用 ./stop.sh 停止应用"
echo "访问 http://localhost:8000 使用应用"
