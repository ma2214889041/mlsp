#!/usr/bin/env python3

import re

def fix_edit_product_redirect(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 替换产品编辑函数中的重定向URL
    pattern = r'(return RedirectResponse\(url=")/admin/products'
    replacement = r'\1/mlsp/admin/products'
    
    modified = re.sub(pattern, replacement, content)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复成功: {file_path}")
        return True
    else:
        print(f"未找到需要修复的重定向URL")
        return False

fix_edit_product_redirect('/home/mlsp/app/api/endpoints/admin.py')
