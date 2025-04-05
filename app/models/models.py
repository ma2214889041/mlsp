from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from .database import Base

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
    stock_threshold = Column(Integer, default=10) 
    order_items = relationship("OrderItem", back_populates="product")
    inventory_items = relationship("Inventory", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    status = Column(String, index=True)  # pending, confirmed, completed, cancelled
    total_amount = Column(Float)
    note = Column(Text, nullable=True)
    pickup_time = Column(String, nullable=True)  # 新增：取货时间
    created_at = Column(DateTime, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)
    
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
    inventory = relationship("Inventory", back_populates="slot", uselist=False)

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
    slot = relationship("ShelfSlot", back_populates="inventory")
    
    def is_expired(self):
        return datetime.now().date() > self.expiry_date
    
    def is_near_expiry(self, days=30):
        return not self.is_expired() and (self.expiry_date - datetime.now().date()).days <= days
