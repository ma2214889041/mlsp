#!/bin/bash
cd /home/mlsp
# 使用--root-path选项确保URL前缀工作正常
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --root-path /mlsp > app.log 2>&1 &
echo $! > app.pid
echo "应用已在后台启动，进程ID保存在app.pid"
