#!/usr/bin/env python3

import os
import re

def fix_image_paths(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找图片和JS中可能的路径问题
    
    # 1. 静态图片URL - 模板中
    img_pattern = r'<img src="\{\{ product\.image_url \}\}"'
    img_replacement = r'<img src="{% if product.image_url.startswith(\'/\') and not product.image_url.startswith(\'/mlsp\') %}/mlsp{{ product.image_url }}{% else %}{{ product.image_url }}{% endif %}"'
    
    # 2. 购物车项目中的图片URL - JS中
    js_img_pattern = r'<img src="\${item\.image}" class="cart-item-img"'
    js_img_replacement = r'<img src="${item.image && item.image.startsWith(\'/\') && !item.image.startsWith(\'/mlsp\') ? \'/mlsp\' + item.image : item.image}" class="cart-item-img"'
    
    # 3. API URL前缀
    api_pattern = r'fetch\(`/client/api/product/\${productId}`\)'
    api_replacement = r'fetch(`/mlsp/client/api/product/${productId}`)'
    
    # 应用替换
    modified_content = content
    modified_content = re.sub(img_pattern, img_replacement, modified_content)
    modified_content = re.sub(js_img_pattern, js_img_replacement, modified_content)
    modified_content = re.sub(api_pattern, api_replacement, modified_content)
    
    if modified_content != content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        
        print(f"已修复文件: {file_path}")
        return True
    else:
        print(f"无需修复: {file_path}")
        return False

# 修复create_order.html中的图片URL
fix_image_paths('/home/mlsp/app/templates/client/create_order.html')
