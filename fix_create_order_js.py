#!/usr/bin/env python3

import os
import re

def fix_add_to_cart_js(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 找到addToCart函数
    add_to_cart_pattern = r'(async function addToCart\(productId\) \{.*?\})'
    add_to_cart_match = re.search(add_to_cart_pattern, content, re.DOTALL)
    
    if not add_to_cart_match:
        print("未找到addToCart函数，改为查找非异步版本")
        add_to_cart_pattern = r'(function addToCart\(productId\) \{.*?\})'
        add_to_cart_match = re.search(add_to_cart_pattern, content, re.DOTALL)
        
        if not add_to_cart_match:
            print("仍未找到addToCart函数")
            return False
    
    func_content = add_to_cart_match.group(1)
    
    # 添加productId检查
    if "if (!productId" not in func_content:
        modified_func = func_content.replace(
            "{",
            "{\n            // 添加productId检查\n            if (!productId || productId === 'undefined') {\n                console.error('无效的产品ID');\n                alert('无法添加产品，请刷新页面重试');\n                return;\n            }\n",
            1  # 只替换第一次出现的
        )
        
        # 替换原函数
        modified_content = content.replace(func_content, modified_func)
        
        with open(file_path, 'w') as f:
            f.write(modified_content)
        
        print("已添加productId检查")
        return True
    else:
        print("addToCart函数可能已经有productId检查")
        return False

fix_add_to_cart_js('/home/mlsp/app/templates/client/create_order.html')
