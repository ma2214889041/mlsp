#!/usr/bin/env python3

import os
import re

def fix_client_api_endpoints(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 检查API响应中图片URL的处理
    image_pattern = r'(return \{.*?"image": )prod\.image_url(,.*?\})'
    image_replacement = r'\1(prod.image_url.startswith("/") and not prod.image_url.startswith("/mlsp") ? "/mlsp" + prod.image_url : prod.image_url)\2'
    
    # 添加错误处理，防止"undefined"值被传入
    error_pattern = r'(product_id: int,.*?)(db: Session = Depends\(get_db\),)'
    error_replacement = r'\1\n    if isinstance(product_id, str) and product_id.lower() == "undefined":\n        return JSONResponse(\n            status_code=400,\n            content={"error": "无效的产品ID"}\n        )\n    \2'
    
    # 应用替换
    modified = content
    modified = re.sub(image_pattern, image_replacement, modified)
    modified = re.sub(error_pattern, error_replacement, modified)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复了文件: {file_path}")
        return True
    else:
        print(f"无需修复: {file_path}")
        return False

# 检查并修复client.py文件
client_endpoint_file = '/home/mlsp/app/api/endpoints/client.py'
fix_client_api_endpoints(client_endpoint_file)
