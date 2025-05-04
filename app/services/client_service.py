from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime

from ..db import models
from ..core.security import verify_password
from ..utils.qrcode_utils import save_order_qrcode

class RestaurantService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_restaurant(self, restaurant_id: int):
        return self.db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()
        
    def get_restaurant_by_username(self, username: str):
        return self.db.query(models.Restaurant).filter(models.Restaurant.username == username).first()
        
    def authenticate(self, username: str, password: str):
        restaurant = self.get_restaurant_by_username(username)
        if not restaurant:
            return None
        if not verify_password(password, restaurant.password):
            return None
        return restaurant
        
    def create_restaurant(self, name: str, address: str, phone: str, username: str, password: str):
        # 检查用户名是否已存在
        if self.get_restaurant_by_username(username):
            return None
            
        # 创建新餐馆
        return models.Restaurant.create(self.db, name, address, phone, username, password)
    
    def get_restaurant_orders(self, restaurant_id: int, status: Optional[str] = None):
        query = self.db.query(models.Order).filter(models.Order.restaurant_id == restaurant_id)
        if status:
            query = query.filter(models.Order.status == status)
        return query.order_by(models.Order.created_at.desc()).all()

class OrderService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_order(self, order_id: int):
        return self.db.query(models.Order).filter(models.Order.id == order_id).first()
    
    def get_order_for_restaurant(self, order_id: int, restaurant_id: int):
        return self.db.query(models.Order).filter(
            models.Order.id == order_id,
            models.Order.restaurant_id == restaurant_id
        ).first()
    
    def get_order_items(self, order_id: int):
        return self.db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
    
    def create_order(self, restaurant_id: int, note: Optional[str] = None):
        db_order = models.Order(
            restaurant_id=restaurant_id,
            status="pending",
            total_amount=0,
            note=note,
            created_at=datetime.datetime.now()
        )
        self.db.add(db_order)
        self.db.commit()
        self.db.refresh(db_order)
        return db_order
    
    def add_order_item(self, order_id: int, product_id: int, quantity: int, unit_price: float, unit_type: Optional[str] = None):
        db_item = models.OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            unit_type=unit_type
        )
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def update_order_total(self, order_id: int):
        order = self.get_order(order_id)
        if not order:
            return None
        
        items = self.get_order_items(order_id)
        total = sum(item.quantity * item.unit_price for item in items)
        
        order.total_amount = total
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def confirm_order(self, order_id: int, pickup_time: Optional[str] = None):
        order = self.get_order(order_id)
        if not order or order.status != "pending":
            return None
        
        # 生成二维码
        qrcode_url = save_order_qrcode(order_id)
        
        order.status = "confirmed"
        order.confirmed_at = datetime.datetime.now()
        order.qrcode_url = qrcode_url
        if pickup_time:
            order.pickup_time = pickup_time
        
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def cancel_order(self, order_id: int, reason: str):
        order = self.get_order(order_id)
        if not order or order.status in ["completed", "cancelled"]:
            return None
        
        # 恢复库存
        product_service = ProductService(self.db)
        items = self.get_order_items(order_id)
        for item in items:
            product = product_service.get_product(item.product_id)
            if product:
                product.stock += item.quantity
        
        order.status = "cancelled"
        order.cancelled_at = datetime.datetime.now()
        order.cancel_reason = reason
        
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def update_order(self, order_id: int, data: Dict[str, Any]):
        order = self.get_order(order_id)
        if not order:
            return None
        
        for key, value in data.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        self.db.commit()
        self.db.refresh(order)
        return order

class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_product(self, product_id: int):
        return self.db.query(models.Product).filter(models.Product.id == product_id).first()
    
    def get_products(self, active_only: bool = False):
        query = self.db.query(models.Product)
        if active_only:
            query = query.filter(models.Product.is_active == True)
        return query.all()
    
    def get_available_products(self):
        return self.db.query(models.Product).filter(
            models.Product.stock > 0,
            models.Product.is_active == True
        ).all()
        
    def get_product_by_barcode(self, barcode: str):
        return self.db.query(models.Product).filter(models.Product.barcode == barcode).first()
    
    def update_product_stock(self, product_id: int, new_stock: int):
        product = self.get_product(product_id)
        if not product:
            return None
        
        product.stock = new_stock
        self.db.commit()
        self.db.refresh(product)
        return product
