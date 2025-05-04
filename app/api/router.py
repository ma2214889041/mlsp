from fastapi import APIRouter

# 创建主路由
api_router = APIRouter()

# 导入并注册路由
from app.api.endpoints.client import router as client_router
from app.api.endpoints.admin import router as admin_router
from app.api.endpoints.common import router as common_router
from app.api.endpoints.employee import router as employee_router
from app.api.endpoints.inventory import router as inventory_router
from app.api.endpoints.barcode import router as barcode_router
from app.api.endpoints.order_recognition import router as order_recognition_router
from app.api.endpoints.order_recognition_client import router as order_recognition_client_router

# 注册路由
api_router.include_router(common_router)
api_router.include_router(client_router, prefix="/client", tags=["client"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(employee_router, prefix="/employee", tags=["employee"])
api_router.include_router(inventory_router, prefix="/admin/api", tags=["inventory"])
api_router.include_router(barcode_router, tags=["barcode"])
api_router.include_router(order_recognition_router)  # 订单识别API
api_router.include_router(order_recognition_client_router)  # 客户端订单识别API
