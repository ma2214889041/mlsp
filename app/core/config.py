import os
from pathlib import Path
from typing import Optional

# 基本路径
BASE_DIR = Path("/home/mlsp")
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
UPLOADS_DIR = STATIC_DIR / "uploads"

# 应用配置
APP_NAME = "米兰食品公司系统"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# 路径前缀配置 - 根据环境变量决定
USE_MLSP_PREFIX = os.environ.get('USE_MLSP_PREFIX', 'true').lower() == 'true'
BASE_PATH = "/mlsp" if USE_MLSP_PREFIX else ""

# 其他配置
DEFAULT_ITEMS_PER_PAGE = 10
NEAR_EXPIRY_DAYS = 30  # 多少天内算即将过期

def get_url(path: Optional[str] = None) -> str:
    """为路径添加正确的前缀"""
    if not path:
        return BASE_PATH
        
    # 去除首尾空格
    path = path.strip()
    
    # 如果路径已经包含前缀或者是完整URL，直接返回
    if path.startswith(BASE_PATH) or path.startswith(("http://", "https://")):
        return path
        
    # 如果路径以斜杠开头，确保不会有双斜杠
    if path.startswith('/'):
        return f"{BASE_PATH}{path}"
    else:
        return f"{BASE_PATH}/{path}"

# 提供更短的别名函数
get_prefixed_url = get_url
