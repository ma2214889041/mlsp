#!/bin/bash
# 此脚本更新代码中生成图片 URL 的部分，
# 将 /static/ 替换为 /mlsp/static/ 以确保图片正确显示。

echo "【1/3】更新管理员端生成产品图片 URL..."
ADMIN_FILE="/home/mlsp/app/api/endpoints/admin.py"
if [ -f "$ADMIN_FILE" ]; then
    sed -i 's|/static/uploads/products/|/mlsp/static/uploads/products/|g' "$ADMIN_FILE"
    echo "更新 $ADMIN_FILE 中的产品图片 URL 完成。"
else
    echo "未找到 $ADMIN_FILE"
fi

echo "【2/3】更新员工端上传订单照片的 URL..."
EMPLOYEE_FILE="/home/mlsp/app/api/endpoints/employee.py"
if [ -f "$EMPLOYEE_FILE" ]; then
    sed -i 's|/static/uploads/order_photos/|/mlsp/static/uploads/order_photos/|g' "$EMPLOYEE_FILE"
    echo "更新 $EMPLOYEE_FILE 中的订单照片 URL 完成。"
else
    echo "未找到 $EMPLOYEE_FILE"
fi

echo "【3/3】更新二维码生成工具中的 URL..."
QR_FILE="/home/mlsp/app/utils/qrcode_utils.py"
if [ -f "$QR_FILE" ]; then
    sed -i 's|/static/qrcodes/|/mlsp/static/qrcodes/|g' "$QR_FILE"
    echo "更新 $QR_FILE 中的二维码图片 URL 完成。"
else
    echo "未找到 $QR_FILE"
fi

echo "所有图片 URL 更新完成，请重启应用以使更改生效。"
