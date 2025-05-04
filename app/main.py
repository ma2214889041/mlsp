from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
import os
import logging
import traceback
from starlette.middleware.base import BaseHTTPMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/mlsp/app_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# 导入配置
from app.core.config import BASE_PATH, get_url

# 创建应用
app = FastAPI(
    title="米兰食品公司订单与仓储系统",
    description="提供餐馆订单管理和仓储功能的系统"
)

# URL前缀中间件
class URLPrefixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 存储原始URL
        request.state.original_path = request.url.path
        
        # 继续处理请求
        response = await call_next(request)
        
        # 如果是重定向响应，确保URL有正确前缀
        if isinstance(response, RedirectResponse):
            # 获取当前重定向目标
            redirect_url = response.headers.get("location", "")
            
            # 如果不是完整URL且不是以BASE_PATH开始，添加前缀
            if not redirect_url.startswith(("http://", "https://")) and BASE_PATH and not redirect_url.startswith(BASE_PATH):
                response.headers["location"] = get_url(redirect_url)
                
        return response

# 应用中间件
app.add_middleware(URLPrefixMiddleware)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = f"URL: {request.url}, Method: {request.method}, Error: {str(exc)}, Traceback: {traceback.format_exc()}"
    logger.error(error_detail)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请联系管理员", "error": str(exc)}
    )

# 确保静态目录存在
def ensure_directories():
    directories = [
        "/home/mlsp/app/static/qrcodes/shelves",
        "/home/mlsp/app/static/qrcodes/slots",
        "/home/mlsp/app/static/uploads/order_photos",
        "/home/mlsp/app/static/uploads/products"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # 设置权限
        os.system(f"chmod -R 777 {directory}")

# 创建数据库表
def setup_database():
    logger.info("创建数据库表...")
    from app.db import models, database
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("数据库表创建完成")

# 挂载API路由
def register_routers():
    logger.info("注册路由...")
    from app.api.router import api_router
    app.include_router(api_router)
    logger.info("路由注册完成")

# 挂载静态文件
def mount_static_files():
    app.mount("/static", StaticFiles(directory="/home/mlsp/app/static"), name="static")

# 全局路由
@app.get("/")
async def root():
    from app.core.deps import redirect_with_prefix
    return redirect_with_prefix("/client")

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    ensure_directories()
    setup_database()
    register_routers()
    mount_static_files()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
