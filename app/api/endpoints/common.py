from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from ...core.config import get_url
from ...core.deps import redirect_with_prefix

router = APIRouter()

# 根路径根据用户类型重定向
@router.get("/")
async def root(request: Request):
    # 检查用户类型
    if request.cookies.get("employee_authenticated") == "true":
        return redirect_with_prefix("/employee/dashboard")
    elif request.cookies.get("admin_authenticated") == "true":
        return redirect_with_prefix("/admin/dashboard")
    elif request.cookies.get("restaurant_id"):
        return redirect_with_prefix("/client/dashboard")
    else:
        return redirect_with_prefix("/client")

# 注销
@router.get("/logout")
async def logout():
    response = redirect_with_prefix("/")
    
    # 删除所有身份验证cookie
    cookies_to_delete = [
        "restaurant_id", "restaurant_name", 
        "admin_authenticated", 
        "employee_authenticated", "employee_id", "employee_name"
    ]
    
    for cookie in cookies_to_delete:
        response.delete_cookie(key=cookie)
        
    return response
