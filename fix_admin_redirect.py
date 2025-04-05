#!/usr/bin/env python3

import re

def fix_redirect_urls(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找 RedirectResponse(url="/admin/products" 并替换为 RedirectResponse(url="/mlsp/admin/products"
    modified = re.sub(r'RedirectResponse\(url="/admin/products"', 'RedirectResponse(url="/mlsp/admin/products"', content)
    
    # 查找编辑产品后的重定向处理
    modified = re.sub(r'(return\s+RedirectResponse\(url=")/admin/products', r'\1/mlsp/admin/products', modified)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复了文件: {file_path}")
        return True
    return False

# 查找并修复admin.py文件
import os

admin_files = [
    '/home/mlsp/app/api/endpoints/admin.py'
]

for file in admin_files:
    if os.path.exists(file):
        fix_redirect_urls(file)
