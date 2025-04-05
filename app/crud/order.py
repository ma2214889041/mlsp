from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
from ..db import models
from ..utils.qrcode_utils import save_order_qrcode

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_order_with_restaurant(db: Session, order_id: int, restaurant_id: int):
    return db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.restaurant_id == restaurant_id
    ).first()

def get_orders(db: Session, skip: int = 0, limit: int = 100, 
              status: Optional[str] = None, restaurant_id: Optional[int] = None):
    query = db.query(models.Order)
    
    if status:
        query = query.filter(models.Order.status == status)
    
    if restaurant_id:
        query = query.filter(models.Order.restaurant_id == restaurant_id)
    
    return query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()

def get_order_items(db: Session, order_id: int):
    return db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()

def create_order(db: Session, restaurant_id: int, note: Optional[str] = None):
    db_order = models.Order(
        restaurant_id=restaurant_id,
        status="pending",
        total_amount=0,  # 将在添加商品后更新
        note=note,
        created_at=datetime.datetime.now()
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def add_order_item(db: Session, order_id: int, product_id: int, 
                  quantity: int, unit_price: float, unit_type: Optional[str] = None):
    # 不包含 is_picked 字段
    db_item = models.OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        unit_type=unit_type
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_order_total(db: Session, order_id: int):
    """更新订单总金额"""
    order = get_order(db, order_id)
    if not order:
        return None
    
    items = get_order_items(db, order_id)
    total = sum(item.quantity * item.unit_price for item in items)
    
    order.total_amount = total
    db.commit()
    db.refresh(order)
    return order

def confirm_order(db: Session, order_id: int, pickup_time: Optional[str] = None):
    """确认订单并生成二维码"""
    order = get_order(db, order_id)
    if not order or order.status != "pending":
        return None
    
    # 生成二维码并保存
    qrcode_url = save_order_qrcode(order_id)
    
    order.status = "confirmed"
    order.confirmed_at = datetime.datetime.now()
    order.qrcode_url = qrcode_url
    if pickup_time:
        order.pickup_time = pickup_time
    
    db.commit()
    db.refresh(order)
    return order

def complete_order(db: Session, order_id: int):
    """完成订单"""
    order = get_order(db, order_id)
    if not order or order.status != "confirmed":
        return None
    
    order.status = "completed"
    order.completed_at = datetime.datetime.now()
    
    db.commit()
    db.refresh(order)
    return order

def cancel_order(db: Session, order_id: int, cancel_reason: str):
    """取消订单"""
    order = get_order(db, order_id)
    if not order or order.status in ["completed", "cancelled"]:
        return None
    
    # 恢复库存
    items = get_order_items(db, order_id)
    for item in items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    
    order.status = "cancelled"
    order.cancelled_at = datetime.datetime.now()
    order.cancel_reason = cancel_reason
    
    db.commit()
    db.refresh(order)
    return order

def update_pickup_time(db: Session, order_id: int, pickup_time: str):
    """更新取货时间"""
    order = get_order(db, order_id)
    if not order:
        return None
    
    order.pickup_time = pickup_time
    db.commit()
    db.refresh(order)
    return order

def update_order(db: Session, order_id: int, data: Dict[str, Any]):
    """更新订单信息"""
    order = get_order(db, order_id)
    if not order:
        return None
    
    for key, value in data.items():
        if hasattr(order, key):
            setattr(order, key, value)
    
    db.commit()
    db.refresh(order)
    return order

def mark_order_item_picked(db: Session, order_item_id: int):
    """标记订单项已取货"""
    item = db.query(models.OrderItem).filter(models.OrderItem.id == order_item_id).first()
    if not item:
        return None
    
    # 暂时不设置 is_picked 字段
    # item.is_picked = True
    db.commit()
    db.refresh(item)
    return item

def check_all_items_picked(db: Session, order_id: int):
    """检查订单的所有项目是否都已取货"""
    # 获取订单项
    items = get_order_items(db, order_id)
    
    # 获取为此订单记录的所有取货记录
    picking_records = db.query(models.PickingRecord).filter(
        models.PickingRecord.order_id == order_id
    ).all()
    
    # 检查每个订单项是否都有相应的取货记录
    for item in items:
        # 计算此订单项的总取货数量
        picked_quantity = sum(
            record.quantity for record in picking_records 
            if db.query(models.Inventory).filter(
                models.Inventory.id == record.inventory_id,
                models.Inventory.product_id == item.product_id
            ).first() is not None
        )
        
        # 如果取货数量小于订单数量，则未全部取货
        if picked_quantity < item.quantity:
            return False
    
    return True

def record_picking(db: Session, order_id: int, inventory_id: int, employee_id: int, quantity: int):
    """记录取货操作"""
    db_record = models.PickingRecord(
        order_id=order_id,
        inventory_id=inventory_id,
        employee_id=employee_id,
        quantity=quantity,
        picked_at=datetime.datetime.now()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record
