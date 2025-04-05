#!/bin/bash
if [ -f /home/mlsp/app.pid ]; then
    pid=$(cat /home/mlsp/app.pid)
    echo "停止进程 $pid"
    kill $pid
    rm /home/mlsp/app.pid
    echo "应用已停止"
else
    echo "找不到PID文件，应用可能没有运行"
fi
