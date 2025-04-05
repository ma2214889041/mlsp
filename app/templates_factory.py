from fastapi.templating import Jinja2Templates
from pathlib import Path

def create_templates():
    # 创建模板引擎
    templates = Jinja2Templates(directory="/home/mlsp/app/templates")
    
    # 添加全局变量，可以在所有模板中使用
    templates.env.globals["root_path"] = "/mlsp"
    
    return templates
