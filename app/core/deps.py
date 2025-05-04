from fastapi import Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, Union

from ..db.database import SessionLocal
from ..core.config import ADMIN_USERNAME, ADMIN_PASSWORD, BASE_PATH, get_url
from ..db import models

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 用户访问控制 - 统一认证函数
def get_current_user(
    request: Request,
    user_type: str = Query(None)
) -> Dict[str, Any]:
    """
    获取当前用户信息，根据user_type返回不同类型的用户
    
    - client: 返回餐馆ID
    - admin: 验证是否是管理员
    - employee: 验证是否是员工
    """
    if user_type == "admin":
        if request.cookies.get("admin_authenticated") != "true":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要管理员权限",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"type": "admin"}
    
    elif user_type == "employee":
        if request.cookies.get("employee_authenticated") != "true":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要员工权限",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "type": "employee",
            "id": request.cookies.get("employee_id"),
            "name": request.cookies.get("employee_name")
        }
    
    else:  # client
        restaurant_id = request.cookies.get("restaurant_id")
        if not restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录或会话已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "type": "client",
            "id": restaurant_id,
            "name": request.cookies.get("restaurant_name")
        }

# 检查是否已登录(客户端)，必须登录
def get_current_restaurant(request: Request) -> str:
    user = get_current_user(request, "client")
    return user["id"]

# 检查是否已登录(客户端)，返回ID或None
def get_current_restaurant_or_none(request: Request) -> Optional[str]:
    try:
        return get_current_restaurant(request)
    except HTTPException:
        return None

# 检查是否已登录(管理端)
def get_current_admin(request: Request) -> bool:
    get_current_user(request, "admin")
    return True

# 检查是否已登录(员工端)
def get_current_employee(request: Request) -> Dict[str, Any]:
    return get_current_user(request, "employee")

# 带前缀的重定向辅助函数
def redirect_with_prefix(path, status_code=303):
    url = get_url(path)
    return RedirectResponse(url=url, status_code=status_code)
