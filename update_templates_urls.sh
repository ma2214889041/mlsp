#!/bin/bash

# 更新所有HTML模板，使用Jinja2模板变量引用基础路径
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/static/|href="{{ base_path }}/static/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|src="/static/|src="{{ base_path }}/static/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|action="/client/|action="{{ base_path }}/client/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|action="/admin/|action="{{ base_path }}/admin/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|action="/employee/|action="{{ base_path }}/employee/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/client/|href="{{ base_path }}/client/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/admin/|href="{{ base_path }}/admin/|g' {} \;
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i 's|href="/employee/|href="{{ base_path }}/employee/|g' {} \;

echo "已更新所有HTML模板中的URL路径"
