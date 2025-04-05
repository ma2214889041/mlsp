#!/bin/bash

# 查看应用日志
echo "==== 应用日志 ===="
tail -n 100 /home/mlsp/app.log

echo
echo "==== 文件变更日志 ===="
tail -n 50 /home/mlsp/file_change.log

echo
echo "==== 调试日志 ===="
tail -n 100 /home/mlsp/app_debug.log
