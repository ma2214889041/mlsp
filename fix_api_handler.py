#!/usr/bin/env python3

import os
import re

def fix_product_api_handler(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 找到获取产品API处理函数
    product_api_pattern = r'(@router\.get\("/api/product/{product_id}"\)\s*async def get_product_info\([^)]*\):.*?return \{.*?\})'
    match = re.search(product_api_pattern, content, re.DOTALL)
    
    if not match:
        print("未找到产品API处理函数")
        return False
    
    func_content = match.group(1)
    
    # 检查是否已经有了错误处理
    if "undefined" in func_content:
        print("API处理函数似乎已经有错误处理了")
        return False
    
    # 添加错误处理代码
    new_func = re.sub(
        r'(@router\.get\("/api/product/{product_id}"\)\s*async def get_product_info\([^)]*\):)',
        r'\1\n    # 添加错误处理，防止undefined值\n    if isinstance(product_id, str) and product_id == "undefined":\n        return JSONResponse(\n            status_code=400,\n            content={"error": "无效的产品ID"}\n        )\n',
        func_content
    )
    
    # 替换原函数
    modified_content = content.replace(func_content, new_func)
    
    with open(file_path, 'w') as f:
        f.write(modified_content)
    
    print("已修复API处理函数")
    return True

fix_product_api_handler('/home/mlsp/app/api/endpoints/client.py')
