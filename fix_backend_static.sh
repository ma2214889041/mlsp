#!/bin/bash
# 此脚本用于更新后端平台模板及代码中的静态文件引用，
# 使其全部带有 /mlsp 前缀，以便与 FastAPI 的 root_path="/mlsp" 配置一致。

echo "【1/5】更新 admin 模板中的静态文件引用..."
find /home/mlsp/app/templates/admin -type f -name "*.html" -exec sed -i \
    -e 's|href="/static/|href="/mlsp/static/|g' \
    -e 's|src="/static/|src="/mlsp/static/|g' \
    {} \;
echo "admin 模板更新完成。"

echo "【2/5】更新 employee 模板中的静态文件引用..."
find /home/mlsp/app/templates/employee -type f -name "*.html" -exec sed -i \
    -e 's|href="/static/|href="/mlsp/static/|g' \
    -e 's|src="/static/|src="/mlsp/static/|g' \
    {} \;
echo "employee 模板更新完成。"

echo "【3/5】更新所有模板中其他静态文件引用（JS、CSS等）..."
find /home/mlsp/app/templates -type f -name "*.html" -exec sed -i \
    -e 's|src="/static/js/employee-pwa-install.js|src="/mlsp/static/js/employee-pwa-install.js|g' \
    -e 's|src="/static/js/pwa-check.js|src="/mlsp/static/js/pwa-check.js|g' \
    {} \;
echo "所有模板中 JS 静态文件引用更新完成。"

echo "【4/5】更新管理员端生成产品图片 URL..."
ADMIN_FILE="/home/mlsp/app/api/endpoints/admin.py"
if [ -f "$ADMIN_FILE" ]; then
    sed -i 's|image_url = f"/static/uploads/products/|image_url = f"/mlsp/static/uploads/products/|g' "$ADMIN_FILE"
    echo "更新 $ADMIN_FILE 中的产品图片 URL 完成。"
else
    echo "未找到 $ADMIN_FILE，请检查路径。"
fi

echo "【5/5】更新二维码生成工具中（如有）静态资源引用..."
QR_FILE="/home/mlsp/app/utils/qrcode_utils.py"
if [ -f "$QR_FILE" ]; then
    # 如果二维码生成中需要修改图片引用路径，请在此添加对应的 sed 命令
    echo "检查 $QR_FILE 中的二维码 URL，当前未做修改。如有问题请手动检查。"
else
    echo "未找到 $QR_FILE，请检查路径。"
fi

echo "所有后端模板及代码中的静态资源引用更新完成，请重启应用以使更改生效。"
