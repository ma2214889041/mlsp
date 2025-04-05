#!/usr/bin/env python3
import os
import re

# 模板目录
templates_dir = "/home/mlsp/app/templates"

# 替换静态文件引用
def fix_static_links(content):
    # 替换 /static/ 为 /mlsp/static/
    content = content.replace('"/static/', '"/mlsp/static/')
    content = content.replace("'/static/", "'/mlsp/static/")
    
    # 替换表单提交路径，确保它们不会缺少/mlsp前缀
    content = content.replace('action="/admin/', 'action="/mlsp/admin/')
    content = content.replace('action="/client/', 'action="/mlsp/client/')
    content = content.replace('action="/employee/', 'action="/mlsp/employee/')
    
    # 替换href链接
    content = content.replace('href="/admin/', 'href="/mlsp/admin/')
    content = content.replace('href="/client/', 'href="/mlsp/client/')
    content = content.replace('href="/employee/', 'href="/mlsp/employee/')
    content = content.replace('href="/logout"', 'href="/mlsp/logout"')
    
    return content

# 递归处理目录中的所有HTML文件
def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                print(f"处理文件: {file_path}")
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 修改内容
                new_content = fix_static_links(content)
                
                # 如果内容有变化，写回文件
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"  已更新: {file_path}")

if __name__ == "__main__":
    process_directory(templates_dir)
    print("所有模板文件更新完成!")
