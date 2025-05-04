from sqlalchemy.orm import Session
import datetime
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import shutil

from ..db import models
from ..core.security import verify_password
from ..core.config import get_url

class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_employee(self, employee_id: int):
        return self.db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    
    def get_employee_by_username(self, username: str):
        return self.db.query(models.Employee).filter(models.Employee.username == username).first()
    
    def authenticate(self, username: str, password: str):
        employee = self.get_employee_by_username(username)
        if not employee or not employee.is_active:
            return None
        if not verify_password(password, employee.password):
            return None
        return employee
    
    def get_pending_orders(self):
        """获取待处理的已确认订单"""
        return self.db.query(models.Order).filter(
            models.Order.status == "confirmed"
        ).order_by(models.Order.confirmed_at.desc()).all()
    
    def get_expiry_alerts(self, days: int = 30):
        """获取即将过期的商品警告"""
        today = datetime.datetime.now().date()
        future = today + datetime.timedelta(days=days)
        
        return self.db.query(models.Inventory).filter(
            models.Inventory.remaining > 0,
            models.Inventory.expiry_date > today,
            models.Inventory.expiry_date <= future
        ).order_by(models.Inventory.expiry_date).limit(10).all()
    
    def record_picking(self, order_id: int, inventory_id: int, employee_id: int, quantity: int):
        """记录取货操作"""
        # 先检查库存是否足够
        inventory = self.db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()
        if not inventory or inventory.remaining < quantity:
            return None
        
        # 更新库存
        inventory.remaining -= quantity
        
        # 记录取货
        picking_record = models.PickingRecord(
            order_id=order_id,
            inventory_id=inventory_id,
            employee_id=employee_id,
            quantity=quantity,
            picked_at=datetime.datetime.now()
        )
        self.db.add(picking_record)
        self.db.commit()
        
        # 更新产品库存
        product = self.db.query(models.Product).filter(models.Product.id == inventory.product_id).first()
        if product:
            product.stock -= quantity
            self.db.commit()
        
        return picking_record
    
    def upload_order_photo(self, order_id: int, employee_id: int, photo_file):
        """上传订单照片"""
        # 检查订单是否存在
        order = self.db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            return None
        
        # 创建保存照片的目录
        photos_dir = Path("/home/mlsp/app/static/uploads/order_photos")
        photos_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置目录权限
        os.system(f"chmod -R 777 {photos_dir}")
        
        # 生成唯一文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"order_{order_id}_{timestamp}.jpg"
        file_path = photos_dir / filename
        
        # 保存照片
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo_file.file, buffer)
        
        # 设置文件权限
        os.system(f"chmod 777 {file_path}")
        
        # 生成照片URL - 使用相对路径
        photo_url = f"/static/uploads/order_photos/{filename}"
        
        # 创建照片记录
        new_photo = models.OrderPhoto(
            order_id=order_id,
            photo_url=photo_url,
            uploaded_by=employee_id,
            uploaded_at=datetime.datetime.now()
        )
        self.db.add(new_photo)
        self.db.commit()
        self.db.refresh(new_photo)
        
        # 返回完整URL
        return get_url(photo_url)
    
    def complete_order(self, order_id: int):
        """完成订单"""
        order = self.db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order or order.status != "confirmed":
            return None
        
        order.status = "completed"
        order.completed_at = datetime.datetime.now()
        self.db.commit()
        
        return order
    
    def add_inventory(self, product_id: int, quantity: int, expiry_date, slot_id: Optional[int] = None, batch_number: Optional[str] = None):
        """添加库存记录"""
        # 获取产品
        product = self.db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            return None
        
        # 生成批次号
        if not batch_number:
            batch_number = f"B{uuid.uuid4().hex[:8].upper()}"
        
        # 创建库存记录
        inventory = models.Inventory(
            product_id=product_id,
            slot_id=slot_id,
            batch_number=batch_number,
            quantity=quantity,
            remaining=quantity,
            unit_type=product.unit_type,
            entry_date=datetime.datetime.now(),
            expiry_date=expiry_date
        )
        self.db.add(inventory)
        
        # 更新产品库存
        product.stock += quantity
        
        self.db.commit()
        self.db.refresh(inventory)
        
        return inventory
    
    def get_recent_inventory_activities(self, limit: int = 10):
        """获取最近的库存活动"""
        return self.db.query(models.Inventory).order_by(
            models.Inventory.entry_date.desc()
        ).limit(limit).all()

    def check_order_photos(self, order_id: int):
        """检查订单是否有照片"""
        return self.db.query(models.OrderPhoto).filter(
            models.OrderPhoto.order_id == order_id
        ).first() is not None
