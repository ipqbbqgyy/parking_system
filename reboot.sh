#!/bin/bash
# reboot_safe.sh

echo -e "\033[34m[1/4] 检查运行中的uWSGI进程...\033[0m"
ps -ef | grep five_class_demo_uwsgi.ini | grep -v grep

echo -e "\n\033[34m[2/4] 优雅重启uWSGI...\033[0m"
# 使用reload信号（不会断开现有连接）
pkill -HUP -f five_class_demo_uwsgi.ini

echo -e "\n\033[34m[3/4] 启动新实例...\033[0m"
# 使用master进程管理模式
/envs/five_class_demo/bin/uwsgi --ini five_class_demo_uwsgi.ini --daemonize=/var/log/uwsgi_reboot.log

echo -e "\n\033[42;1m[4/4] 重启完成，验证进程:\033[0m"
sleep 1
ps -ef | grep five_class_demo_uwsgi.ini | grep -v grep