#!/bin/bash
# stop_safe.sh

echo -e "\033[34m[1/3] 检查运行进程...\033[0m"
ps -ef | grep five_class_demo_uwsgi.ini | grep -v grep

echo -e "\n\033[34m[2/3] 优雅停止...\033[0m"
# 使用SIGTERM信号允许完成当前请求
pkill -TERM -f five_class_demo_uwsgi.ini
sleep 3  # 等待请求完成

echo -e "\n\033[34m[3/3] 强制清理残留...\033[0m"
