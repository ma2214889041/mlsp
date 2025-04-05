#!/bin/bash
# 此脚本用于更新管理员端上传产品图片时生成的 URL，
# 将生成的图片 URL 前缀从 "/static/uploads/products/" 修改为 "/mlsp/static/uploads/products/"

ADMIN_FILE="/home/mlsp/app/api/endpoints/admin.py"
if [ -f "$ADMIN_FILE" ]; then
    echo "更新 $ADMIN_FILE 中的产品图片 URL 前缀..."
    sed -i 's|image_url = f"/static/uploads/products/|image_url = f"/mlsp/static/uploads/products/|g' "$ADMIN_FILE"
    echo "更新完成。"
else
    echo "未找到 $ADMIN_FILE，请检查路径。"
fi

# 提示：如果数据库中已有产品记录存储了旧的图片 URL，
# 可以用下面的 SQL 语句更新（假设使用的是 SQLite）：
echo "如果数据库中已有旧的图片 URL，请在数据库中执行："
echo "UPDATE products SET image_url = REPLACE(image_url, '/static/uploads/products/', '/mlsp/static/uploads/products/');"
