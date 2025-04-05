#!/usr/bin/env python3

import re

def fix_image_processing(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找处理图片的代码段
    pattern = r'(# 处理图片上传\s+image_url = product_obj\.image_url\s+if image and image\.filename:.*?image_url = )f"([^"]+)"'
    
    # 修改为确保不包含/mlsp前缀的版本
    replacement = r'\1f"/static/uploads/products/{image.filename}"'
    
    modified = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复了图片处理: {file_path}")
        return True
    else:
        print(f"无需修复图片处理: {file_path}")
        return False

fix_image_processing('/home/mlsp/app/api/endpoints/admin.py')
