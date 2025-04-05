from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..core.config import ADMIN_USERNAME, ADMIN_PASSWORD, BASE_PATH

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 检查是否已登录(客户端)，必须登录
def get_current_restaurant(request: Request):
    restaurant_id = request.cookies.get("restaurant_id")
    if not restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return restaurant_id

# 检查是否已登录(客户端)，返回ID或None
def get_current_restaurant_or_none(request: Request):
    return request.cookies.get("restaurant_id")

# 检查是否已登录(管理端)
def get_current_admin(request: Request):
    is_authenticated = request.cookies.get("admin_authenticated") == "true"
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return is_authenticated

# 检查是否已登录(员工端)
def get_current_employee(request: Request):
    is_authenticated = request.cookies.get("employee_authenticated") == "true"
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return is_authenticated

# 获取基础路径，用于模板中的URL构建
def get_base_path():
    return BASE_PATH
