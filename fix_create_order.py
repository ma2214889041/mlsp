#!/usr/bin/env python3

import os
import re

def fix_client_create_order(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 修复1: 检查产品API URL是否正确包含/mlsp前缀
    api_pattern = r'fetch\(`/client/api/product/(\$\{[^}]+\})`\)'
    api_replacement = r'fetch(`/mlsp/client/api/product/\1`)'
    
    # 修复2: 确保产品图片URL正确
    img_pattern = r'<img\s+src="\${([^}]+)}"\s+'
    img_replacement = r'<img src="${\1.startsWith(\'/\') ? \'/mlsp\' + \1 : \1}" '
    
    # 修复3: 确保购物车中的图片URL正确
    cart_img_pattern = r'<img\s+src="\${item\.image}"\s+'
    cart_img_replacement = r'<img src="${item.image.startsWith(\'/\') ? \'/mlsp\' + item.image : item.image}" '
    
    # 应用所有替换
    modified = content
    modified = re.sub(api_pattern, api_replacement, modified)
    modified = re.sub(img_pattern, img_replacement, modified)
    modified = re.sub(cart_img_pattern, cart_img_replacement, modified)
    
    if content != modified:
        with open(file_path, 'w') as f:
            f.write(modified)
        print(f"修复了文件: {file_path}")
        return True
    else:
        print(f"无需修复: {file_path}")
        return False

# 修复创建订单页面
fix_client_create_order('/home/mlsp/app/templates/client/create_order.html')
