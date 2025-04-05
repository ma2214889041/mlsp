#!/bin/bash

echo "请选择部署模式:"
echo "1) 直接IP访问模式 (不使用/mlsp前缀)"
echo "2) ritmohub.cn托管模式 (使用/mlsp前缀)"
read -p "请输入选项 [1/2]: " option

case $option in
    1)
        echo "设置为直接IP访问模式..."
        bash /home/mlsp/fix_url_paths.sh
        ;;
    2)
        echo "设置为ritmohub.cn托管模式..."
        bash /home/mlsp/fix_url_paths.sh mlsp
        ;;
    *)
        echo "无效选项，请输入1或2"
        exit 1
        ;;
esac

echo "部署模式已设置完成"
