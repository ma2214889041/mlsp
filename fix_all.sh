#!/bin/bash
# 此脚本统一更新所有模板中的 URL 链接为带 /mlsp 前缀，
# 并修正管理员端上传产品时生成的图片 URL，确保全部带有 /mlsp 前缀。

echo "【1/2】更新模板中的 URL 链接，使其全部带有 /mlsp 前缀..."
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i \
    -e 's|href="/static/|href="/mlsp/static/|g' \
    -e 's|src="/static/|src="/mlsp/static/|g' \
    -e 's|action="/admin/|action="/mlsp/admin/|g' \
    -e 's|action="/client/|action="/mlsp/client/|g' \
    -e 's|action="/employee/|action="/mlsp/employee/|g' \
    -e 's|href="/admin/|href="/mlsp/admin/|g' \
    -e 's|href="/client/|href="/mlsp/client/|g' \
    -e 's|href="/employee/|href="/mlsp/employee/|g' \
    {} \;
echo "模板 URL 更新完成。"

echo "【2/2】更新管理员端上传产品时生成的图片 URL..."
ADMIN_FILE="/home/mlsp/app/api/endpoints/admin.py"
if [ -f "$ADMIN_FILE" ]; then
    # 替换生成产品图片 URL 的代码，使图片地址带上 /mlsp 前缀
    sed -i 's|image_url = f"/static/uploads/products/|image_url = f"/mlsp/static/uploads/products/|g' "$ADMIN_FILE"
    echo "管理员端文件 $ADMIN_FILE 更新完成。"
else
    echo "未找到 $ADMIN_FILE 文件，请检查路径。"
fi

echo "所有更新已完成，请重启应用以使更改生效。"
