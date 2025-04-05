from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import logging
import traceback

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

# 创建应用 - 设置root_path为/mlsp
app = FastAPI(title="米兰食品公司订单与仓储系统", root_path="/mlsp")

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
os.makedirs("/home/mlsp/app/static/qrcodes/shelves", exist_ok=True)
os.makedirs("/home/mlsp/app/static/qrcodes/slots", exist_ok=True)
os.makedirs("/home/mlsp/app/static/uploads/order_photos", exist_ok=True)
os.makedirs("/home/mlsp/app/static/uploads/products", exist_ok=True)

# 设置所有目录权限
for path in ["/home/mlsp/app/static", "/home/mlsp/app/static/qrcodes", 
             "/home/mlsp/app/static/uploads", "/home/mlsp/app/static/qrcodes/shelves",
             "/home/mlsp/app/static/qrcodes/slots", "/home/mlsp/app/static/uploads/order_photos",
             "/home/mlsp/app/static/uploads/products"]:
    os.system(f"chmod -R 777 {path}")

# 创建数据库表
logger.info("创建数据库表...")
from app.db import models, database
models.Base.metadata.create_all(bind=database.engine)
logger.info("数据库表创建完成")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="/home/mlsp/app/static"), name="static")

# 导入并注册路由
logger.info("注册路由...")
from app.api.endpoints.client import router as client_router
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.common import router as common_router
from app.api.endpoints.employee import router as employee_router
from app.api.endpoints.inventory import router as inventory_router
from app.api.endpoints.barcode import router as barcode_router  # 新增条形码路由

# 修改路由注册顺序和前缀
app.include_router(common_router)
app.include_router(client_router, prefix="/client", tags=["client"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(employee_router, prefix="/employee", tags=["employee"])
app.include_router(inventory_router, prefix="/admin/api", tags=["inventory"])
app.include_router(barcode_router, tags=["barcode"])
logger.info("路由注册完成")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
