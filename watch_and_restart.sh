#!/bin/bash

# 设置要监控的目录
WATCH_DIR="/home/mlsp/app"

# 日志文件
LOG_FILE="/home/mlsp/file_change.log"

# 停止应用函数
stop_app() {
    echo "$(date): 停止应用..." | tee -a $LOG_FILE
    if [ -f /home/mlsp/app.pid ]; then
        pid=$(cat /home/mlsp/app.pid)
        echo "$(date): 停止进程 $pid" | tee -a $LOG_FILE
        kill $pid
        rm /home/mlsp/app.pid
        echo "$(date): 应用已停止" | tee -a $LOG_FILE
    else
        echo "$(date): 找不到PID文件，应用可能没有运行" | tee -a $LOG_FILE
    fi
}

# 启动应用函数
start_app() {
    echo "$(date): 启动应用..." | tee -a $LOG_FILE
    cd /home/mlsp
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
    echo $! > app.pid
    echo "$(date): 应用已在后台启动，进程ID保存在app.pid" | tee -a $LOG_FILE
}

# 重启应用函数
restart_app() {
    echo "$(date): 检测到文件变更，重启应用..." | tee -a $LOG_FILE
    stop_app
    sleep 2
    start_app
}

# 首次启动应用
if [ ! -f /home/mlsp/app.pid ]; then
    start_app
fi

echo "$(date): 开始监控 $WATCH_DIR 目录下的 .py 文件变更..." | tee -a $LOG_FILE

# 使用 inotifywait 监控 Python 文件变更
# 如果系统没有安装 inotify-tools，需要先安装：
# apt-get update && apt-get install -y inotify-tools

while true; do
    # 监控所有 .py 文件的变更
    changes=$(find $WATCH_DIR -name "*.py" -type f -exec stat --format="%Y %n" {} \; | sort)
    
    sleep 5
    
    new_changes=$(find $WATCH_DIR -name "*.py" -type f -exec stat --format="%Y %n" {} \; | sort)
    
    if [ "$changes" != "$new_changes" ]; then
        changed_files=$(diff <(echo "$changes") <(echo "$new_changes") | grep ">" | cut -d' ' -f3-)
        echo "$(date): 检测到文件变更: $changed_files" | tee -a $LOG_FILE
        restart_app
    fi
done
