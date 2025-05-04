from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
import shutil
import os

from ..db import models
from ..core.security import verify_password, get_password_hash
from ..core.config import ADMIN_USERNAME, ADMIN_PASSWORD

class AdminService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate(self, username: str, password: str) -> bool:
        """验证管理员账户"""
        return username == ADMIN_USERNAME and password == ADMIN_PASSWORD
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        # 获取待处理订单数量
        pending_orders = self.db.query(models.Order).filter(models.Order.status == "pending").count()
        
        # 获取产品总数
        total_products = self.db.query(models.Product).count()
        
        # 获取餐馆总数
        total_restaurants = self.db.query(models.Restaurant).count()
        
        # 获取最新订单
        latest_orders = self.db.query(models.Order).order_by(models.Order.created_at.desc()).limit(5).all()
        
        # 获取库存预警产品
        low_stock_products = self.db.query(models.Product).filter(
            models.Product.stock <= models.Product.stock_threshold
        ).order_by(models.Product.stock).limit(5).all()
        
        return {
            "pending_orders": pending_orders,
            "total_products": total_products,
            "total_restaurants": total_restaurants,
            "latest_orders": latest_orders,
            "low_stock_products": low_stock_products
        }
    
    def get_orders(self, status: Optional[str] = None, restaurant_id: Optional[int] = None):
        """获取订单列表"""
        query = self.db.query(models.Order)
        
        if status:
            query = query.filter(models.Order.status == status)
        
        if restaurant_id:
            query = query.filter(models.Order.restaurant_id == restaurant_id)
        
        return query.order_by(models.Order.created_at.desc()).all()
    
    def get_employees(self):
        """获取所有员工"""
        return self.db.query(models.Employee).all()
    
    def create_employee(self, name: str, username: str, password: str, position: Optional[str] = None, 
                        phone: Optional[str] = None, is_active: bool = True):
        """创建员工"""
        existing = self.db.query(models.Employee).filter(models.Employee.username == username).first()
        if existing:
            return None
            
        return models.Employee.create(self.db, name, username, password, position, phone, is_active)
    
    def update_employee(self, employee_id: int, **kwargs):
        """更新员工信息"""
        employee = self.db.query(models.Employee).filter(models.Employee.id == employee_id).first()
        if not employee:
            return None
            
        # 处理密码更新
        if 'password' in kwargs and kwargs['password']:
            kwargs['password'] = get_password_hash(kwargs['password'])
        elif 'password' in kwargs:
            # 如果密码为空，则不更新密码
            del kwargs['password']
            
        for key, value in kwargs.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
                
        self.db.commit()
        self.db.refresh(employee)
        return employee
        
    def delete_employee(self, employee_id: int):
        """删除员工"""
        employee = self.db.query(models.Employee).filter(models.Employee.id == employee_id).first()
        if employee:
            self.db.delete(employee)
            self.db.commit()
            return True
        return False
        
    def save_product_image(self, file):
        """保存产品图片"""
        file_location = f"/home/mlsp/app/static/uploads/products/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 设置文件权限
        os.chmod(file_location, 0o777)
        
        # 返回相对URL
        return f"/static/uploads/products/{file.filename}"
