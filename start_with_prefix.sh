#!/bin/bash
export USE_MLSP_PREFIX=false
cd /home/mlsp
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
echo $! > app.pid
echo "应用已在后台启动，进程ID保存在app.pid"
