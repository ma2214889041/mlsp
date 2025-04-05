#!/bin/bash

# 更新所有路由器文件
for file in /home/mlsp/app/api/endpoints/*.py; do
    if [ -f "$file" ]; then
        # 备份原文件
        cp "$file" "${file}.bak"
        
        # 替换模板初始化代码
        sed -i 's|templates = Jinja2Templates(directory="/home/mlsp/app/templates")|from ...templates_factory import create_templates\ntemplates = create_templates()|g' "$file"
        
        # 添加BASE_PATH导入
        sed -i '1s|^|from ...core.config import BASE_PATH\n|' "$file"
        
        echo "已更新路由器: $file"
    fi
done

echo "所有路由器文件已更新"
