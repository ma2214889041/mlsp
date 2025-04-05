from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
import urllib.parse

router = APIRouter()

# 根路径根据用户类型重定向
@router.get("/")
async def root(request: Request):
    # 检查用户类型
    if request.cookies.get("employee_authenticated") == "true":
        return RedirectResponse(url="/mlsp/employee/dashboard")
    elif request.cookies.get("admin_authenticated") == "true":
        return RedirectResponse(url="/mlsp/admin/dashboard")
    elif request.cookies.get("restaurant_id"):
        return RedirectResponse(url="/mlsp/client/dashboard")
    else:
        return RedirectResponse(url="/mlsp/client")

# 注销
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/mlsp")
    response.delete_cookie(key="restaurant_id")
    response.delete_cookie(key="restaurant_name")
    response.delete_cookie(key="admin_authenticated")
    response.delete_cookie(key="employee_authenticated")
    response.delete_cookie(key="employee_id")
    response.delete_cookie(key="employee_name")
    return response
