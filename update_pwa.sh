#!/bin/bash

# 更新PWA相关文件和设置
echo "开始更新PWA配置..."

# 创建必要的目录
mkdir -p /home/mlsp/app/static/icons
mkdir -p /home/mlsp/app/static/css
mkdir -p /home/mlsp/app/static/js

# 运行更新脚本
bash /home/mlsp/update_pwa_headers.sh
bash /home/mlsp/add_mobile_css.sh
bash /home/mlsp/add_pwa_mode.sh
bash /home/mlsp/add_install_prompt.sh

# 重启应用
bash /home/mlsp/stop.sh
bash /home/mlsp/start.sh

echo "PWA设置更新完成！您的应用现在应该具有更好的原生应用体验。"
