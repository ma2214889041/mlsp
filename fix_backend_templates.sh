#!/bin/bash
# 此脚本用于更新后端平台模板中的 URL，
# 确保所有链接均带有 /mlsp 前缀。

echo "更新 admin 模板..."
find /home/mlsp/app/templates/admin -type f -name "*.html" -exec sed -i \
    -e 's|href="/admin/|href="/mlsp/admin/|g' \
    -e 's|action="/admin/|action="/mlsp/admin/|g' \
    -e 's|href="/static/|href="/mlsp/static/|g' \
    -e 's|src="/static/|src="/mlsp/static/|g' \
    -e 's|href="/logout"|href="/mlsp/logout"|g' \
    {} \;
echo "admin 模板更新完成。"

echo "更新 employee 模板..."
find /home/mlsp/app/templates/employee -type f -name "*.html" -exec sed -i \
    -e 's|href="/employee/|href="/mlsp/employee/|g' \
    -e 's|action="/employee/|action="/mlsp/employee/|g' \
    -e 's|href="/static/|href="/mlsp/static/|g' \
    -e 's|src="/static/|src="/mlsp/static/|g' \
    {} \;
echo "employee 模板更新完成。"

echo "更新 common 和其他后端模板..."
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i \
    -e 's|href="/logout"|href="/mlsp/logout"|g' \
    {} \;
echo "其他后端模板更新完成。"

echo "后端平台所有模板更新已完成，请重启应用以使更改生效。"
