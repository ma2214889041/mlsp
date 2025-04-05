#!/usr/bin/env python3

import os
import re

def search_edit_product_handler():
    file_path = '/home/mlsp/app/api/endpoints/admin.py'
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 查找 admin_edit_product_post 函数
    edit_product_pattern = r'async def admin_edit_product_post\([^)]*\):(.*?)def'
    match = re.search(edit_product_pattern, content, re.DOTALL)
    
    if match:
        function_body = match.group(1)
        # 查找重定向语句
        redirect_pattern = r'(RedirectResponse\(url=")([^"]*)'
        redirect_match = re.search(redirect_pattern, function_body)
        
        if redirect_match:
            full_redirect = redirect_match.group(0)
            redirect_url = redirect_match.group(2)
            print(f"找到重定向URL: {redirect_url}")
            
            # 如果需要修复，输出修复建议
            if not redirect_url.startswith('/mlsp/'):
                print(f"需要修复为: {redirect_match.group(1)}/mlsp{redirect_url}")
                return True
        else:
            print("未找到重定向语句")
    else:
        print("未找到编辑产品的POST处理函数")
    
    return False

result = search_edit_product_handler()
print(f"是否需要修复: {result}")
