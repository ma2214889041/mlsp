#!/bin/bash

# 检查命令行参数
if [ "$1" == "mlsp" ]; then
    echo "设置为使用 /mlsp 前缀 (用于 ritmohub.cn 部署)"
    export USE_MLSP_PREFIX=true
    PREFIX="/mlsp"
else
    echo "设置为使用根路径 (用于直接IP访问)"
    export USE_MLSP_PREFIX=false
    PREFIX=""
fi

# 创建启动脚本
cat > /home/mlsp/start_with_prefix.sh << EOL
#!/bin/bash
export USE_MLSP_PREFIX=$USE_MLSP_PREFIX
cd /home/mlsp
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
echo \$! > app.pid
echo "应用已在后台启动，进程ID保存在app.pid"
EOL

chmod +x /home/mlsp/start_with_prefix.sh

# 修改模板工厂
cat > /home/mlsp/app/templates_factory.py << EOL
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.core.config import BASE_PATH

# 创建模板引擎并添加全局变量
def create_templates(directory: str = "/home/mlsp/app/templates"):
    templates = Jinja2Templates(directory=directory)
    templates.env.globals["base_path"] = BASE_PATH
    return templates
EOL

# 停止当前应用
bash /home/mlsp/stop.sh

# 使用新的启动脚本启动应用
bash /home/mlsp/start_with_prefix.sh

echo "应用已重启，使用前缀: $PREFIX"
