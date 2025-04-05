#!/bin/bash

# 将移动CSS添加到所有模板
for dir in client admin employee; do
  for file in /home/mlsp/app/templates/$dir/*.html; do
    # 检查文件是否已经包含移动CSS
    if ! grep -q "mobile-app.css" "$file"; then
      # 在</head>标签前插入CSS链接
      sed -i '/<\/head>/i <link rel="stylesheet" href="/static/css/mobile-app.css">' "$file"
      echo "已添加移动CSS到 $file"
    else
      echo "文件 $file 已包含移动CSS"
    fi
  done
done

echo "所有模板移动CSS添加完成！"
