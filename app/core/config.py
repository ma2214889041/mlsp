import os
from pathlib import Path

# 基本路径
BASE_DIR = Path("/home/mlsp")
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
UPLOADS_DIR = STATIC_DIR / "uploads"

# 确保上传目录存在
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "products").mkdir(exist_ok=True)

# 应用配置
APP_NAME = "米兰食品公司系统"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword"

# 路径前缀配置 - 根据环境变量决定
# 如果是在ritmohub.cn上运行，使用/mlsp前缀，否则使用空字符串
USE_MLSP_PREFIX = os.environ.get('USE_MLSP_PREFIX', 'false').lower() == 'true'
BASE_PATH = "/mlsp" if USE_MLSP_PREFIX else ""

# 其他配置
DEFAULT_ITEMS_PER_PAGE = 10
NEAR_EXPIRY_DAYS = 30  # 多少天内算即将过期
