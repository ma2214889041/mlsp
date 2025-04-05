#!/usr/bin/env python3

import os
import re

def fix_image_urls_in_template(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找图片引用模式
    pattern = r'<img\s+src="{{ *([^}]+) *}}"'
    
    # 检查是否已经添加了前缀处理
    if 'product.image_url.startswith(\'/mlsp\')' in content:
        print(f"文件已经包含前缀处理: {file_path}")
        return False
    
    # 替换为包含条件判断的版本
    replacement = r'''<img src="{% if \1 and not \1.startswith('/mlsp') and not \1.startswith('http') %}/mlsp{{ \1 }}{% else %}{{ \1 }}{% endif %}"'''
    
    modified = re.sub(pattern, replacement, content)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复了文件: {file_path}")
        return True
    else:
        print(f"无需修复: {file_path}")
        return False

# 修复客户端模板
client_templates = [
    '/home/mlsp/app/templates/client/index.html',
    '/home/mlsp/app/templates/client/products.html',
    '/home/mlsp/app/templates/client/create_order.html',
    '/home/mlsp/app/templates/client/edit_order.html'
]

for template in client_templates:
    fix_image_urls_in_template(template)
