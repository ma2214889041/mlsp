#!/usr/bin/env python3

import os
import re

def fix_static_paths(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换 /static/ 为 /mlsp/static/
    modified = re.sub(r'(href|src)="(/static/[^"]*)"', r'\1="/mlsp\2"', content)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复了文件: {file_path}")

# 修复特定模板
fix_static_paths('/home/mlsp/app/templates/admin/edit_product.html')
