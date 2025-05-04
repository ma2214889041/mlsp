from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.db.database import Base
from app.core.security import get_password_hash

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    phone = Column(String)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    
    orders = relationship("Order", back_populates="restaurant")
    
    @classmethod
    def create(cls, db, name, address, phone, username, password):
        hashed_password = get_password_hash(password)
        restaurant = cls(
            name=name,
            address=address,
            phone=phone,
            username=username,
            password=hashed_password
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        return restaurant

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float)
    stock = Column(Integer, default=0)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    unit_type = Column(String, default="份")  # 添加单位类型，如：箱、瓶、袋等
    expiry_days = Column(Integer, default=180, nullable=True)  # 默认保质期(天)
    stock_threshold = Column(Integer, default=10)  # 库存阈值，低于此值触发补货建议
    barcode = Column(String, nullable=True, index=True)  # 产品条形码
    
    order_items = relationship("OrderItem", back_populates="product")
    inventory_items = relationship("Inventory", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    status = Column(String, index=True)  # pending, confirmed, completed, cancelled
    total_amount = Column(Float)
    note = Column(Text, nullable=True)
    pickup_time = Column(String, nullable=True)  # 取货时间
    created_at = Column(DateTime, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)
    qrcode_url = Column(String, nullable=True)  # 二维码图片URL
    
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    photos = relationship("OrderPhoto", back_populates="order", cascade="all, delete-orphan")
    picking_records = relationship("PickingRecord", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    unit_type = Column(String, nullable=True)  # 例如：箱、瓶、袋等
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Shelf(Base):
    __tablename__ = "shelves"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)  # 货架位置描述
    created_at = Column(DateTime, default=datetime.now)
    
    slots = relationship("ShelfSlot", back_populates="shelf", cascade="all, delete-orphan")

class ShelfSlot(Base):
    __tablename__ = "shelf_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id"))
    position = Column(String)  # 货位标识，如A1, B2等
    created_at = Column(DateTime, default=datetime.now)
    
    shelf = relationship("Shelf", back_populates="slots")
    # 一个货位可以有多个库存记录
    inventories = relationship("Inventory", back_populates="slot")

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    slot_id = Column(Integer, ForeignKey("shelf_slots.id"), nullable=True)
    batch_number = Column(String, index=True)  # 批次号
    quantity = Column(Integer)  # 数量
    remaining = Column(Integer)  # 剩余数量
    unit_type = Column(String, nullable=True)  # 单位类型
    entry_date = Column(DateTime, index=True)  # 入库日期
    expiry_date = Column(Date, index=True)  # 过期日期
    
    product = relationship("Product", back_populates="inventory_items")
    slot = relationship("ShelfSlot", back_populates="inventories")
    picking_records = relationship("PickingRecord", back_populates="inventory", cascade="all, delete-orphan")
    
    def is_expired(self):
        return datetime.now().date() > self.expiry_date
    
    def is_near_expiry(self, days=30):
        return not self.is_expired() and (self.expiry_date - datetime.now().date()).days <= days

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    position = Column(String, nullable=True)  # 职位
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    picking_records = relationship("PickingRecord", back_populates="employee")
    order_photos = relationship("OrderPhoto", back_populates="employee")
    
    @classmethod
    def create(cls, db, name, username, password, position=None, phone=None, is_active=True):
        hashed_password = get_password_hash(password)
        employee = cls(
            name=name,
            username=username,
            password=hashed_password,
            position=position,
            phone=phone,
            is_active=is_active,
            created_at=datetime.now()
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        return employee

class PickingRecord(Base):
    __tablename__ = "picking_records"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    quantity = Column(Integer)  # 取货数量
    picked_at = Column(DateTime, default=datetime.now)
    
    order = relationship("Order", back_populates="picking_records")
    inventory = relationship("Inventory", back_populates="picking_records")
    employee = relationship("Employee", back_populates="picking_records")

class OrderPhoto(Base):
    __tablename__ = "order_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    photo_url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)
    uploaded_by = Column(Integer, ForeignKey("employees.id"))
    
    order = relationship("Order", back_populates="photos")
    employee = relationship("Employee", back_populates="order_photos")

class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    alert_type = Column(String)  # "low_stock", "expiry"
    message = Column(String)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)
    
    product = relationship("Product")
