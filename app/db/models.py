from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.db.database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    phone = Column(String)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    
    orders = relationship("Order", back_populates="restaurant")

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
    barcode = Column(String, nullable=True, index=True)  # 新增：产品条形码
    
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
    items = relationship("OrderItem", back_populates="order")

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
    # 修改：一个货位可以有多个库存记录，因此改为one-to-many关系
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
    # 修改：每个库存记录属于一个货位，允许多个库存记录关联到同一个货位
    slot = relationship("ShelfSlot", back_populates="inventories")
    
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

# 添加取货记录表
class PickingRecord(Base):
    __tablename__ = "picking_records"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    quantity = Column(Integer)  # 取货数量
    picked_at = Column(DateTime, default=datetime.now)
    
    order = relationship("Order")
    inventory = relationship("Inventory")
    employee = relationship("Employee")

class OrderPhoto(Base):
    __tablename__ = "order_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    photo_url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)
    uploaded_by = Column(Integer, ForeignKey("employees.id"))
    
    order = relationship("Order")
    employee = relationship("Employee")

# 新增表：库存警报日志
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
