#!/bin/bash

# 更新所有HTML文件中的路径，添加/mlsp/前缀
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/static/|href="/mlsp/static/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|src="/static/|src="/mlsp/static/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|action="/client/|action="/mlsp/client/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|action="/admin/|action="/mlsp/admin/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|action="/employee/|action="/mlsp/employee/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/client/|href="/mlsp/client/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/admin/|href="/mlsp/admin/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/employee/|href="/mlsp/employee/|g' {} \;

echo "已更新所有HTML文件中的路径前缀"

# 运行其他更新脚本
bash /home/mlsp/update_pwa_headers.sh
bash /home/mlsp/add_pwa_guide.sh
bash /home/mlsp/add_pwa_styles.sh
bash /home/mlsp/add_sw_register.sh

# 重启应用
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "PWA路径更新完成，应用已重启"
