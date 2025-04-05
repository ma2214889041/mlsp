#!/usr/bin/env python3

import os
import re

def find_add_to_cart_function(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找添加到购物车的函数
    add_to_cart_pattern = r'function addToCart\(productId\).*?\}'
    add_to_cart_match = re.search(add_to_cart_pattern, content, re.DOTALL)
    
    if add_to_cart_match:
        print("找到addToCart函数:\n")
        print(add_to_cart_match.group(0))
    else:
        print("未找到addToCart函数")

find_add_to_cart_function('/home/mlsp/app/templates/client/create_order.html')
