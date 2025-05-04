from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
import uuid
from ..db import models
from ..core.config import NEAR_EXPIRY_DAYS

def get_inventory(db: Session, inventory_id: int):
    return db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()

def get_product_inventory(db: Session, product_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Inventory)\
        .filter(models.Inventory.product_id == product_id, models.Inventory.remaining > 0)\
        .order_by(models.Inventory.entry_date)\
        .offset(skip).limit(limit).all()

def create_inventory(
    db: Session, product_id: int, slot_id: Optional[int], 
    quantity: int, unit_type: str, expiry_date: datetime.date,
    batch_number: Optional[str] = None
):
    # 如果没有提供批次号则生成一个
    if not batch_number:
        batch_number = f"B{uuid.uuid4().hex[:8].upper()}"
    
    db_inventory = models.Inventory(
        product_id=product_id,
        slot_id=slot_id,
        batch_number=batch_number,
        quantity=quantity,
        remaining=quantity,
        unit_type=unit_type,
        entry_date=datetime.datetime.now(),
        expiry_date=expiry_date
    )
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    
    # 更新产品总库存
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        product.stock += quantity
        db.commit()
    
    return db_inventory

def update_inventory_remaining(db: Session, inventory_id: int, used_quantity: int):
    inventory = get_inventory(db, inventory_id)
    if not inventory or inventory.remaining < used_quantity:
        return None
    
    inventory.remaining -= used_quantity
    db.commit()
    db.refresh(inventory)
    return inventory

def get_fifo_picking_suggestions(db: Session, product_id: int, quantity: int):
    """基于先进先出原则获取取货建议"""
    inventory_items = db.query(models.Inventory)\
        .filter(
            models.Inventory.product_id == product_id,
            models.Inventory.remaining > 0
        )\
        .order_by(models.Inventory.expiry_date, models.Inventory.entry_date)\
        .all()
    
    suggestions = []
    remaining_quantity = quantity
    
    for item in inventory_items:
        if remaining_quantity <= 0:
            break
        
        pick_qty = min(remaining_quantity, item.remaining)
        
        # 获取货位信息
        shelf_info = None
        if item.slot:
            shelf = item.slot.shelf
            shelf_info = {
                "shelf_id": shelf.id,
                "shelf_name": shelf.name,
                "shelf_location": item.slot.position
            }
        
        suggestions.append({
            "inventory_id": item.id,
            "batch_number": item.batch_number,
            "quantity": pick_qty,
            "unit_type": item.unit_type,
            "entry_date": item.entry_date.strftime("%Y-%m-%d"),
            "expiry_date": item.expiry_date.strftime("%Y-%m-%d"),
            "is_expired": item.is_expired(),
            "is_near_expiry": item.is_near_expiry(NEAR_EXPIRY_DAYS),
            "shelf_info": shelf_info
        })
        
        remaining_quantity -= pick_qty
    
    return {
        "suggestions": suggestions,
        "remaining_unfulfilled": remaining_quantity if remaining_quantity > 0 else 0
    }

def get_inventory_for_order(db: Session, order_id: int):
    """为订单中的所有商品获取FIFO取货建议"""
    order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
    
    all_suggestions = []
    
    for item in order_items:
        result = get_fifo_picking_suggestions(db, item.product_id, item.quantity)
        
        for suggestion in result["suggestions"]:
            # 添加产品信息
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            suggestion["product_id"] = item.product_id
            suggestion["product_name"] = product.name if product else "未知产品"
            suggestion["picked"] = False  # 我们暂时假定所有项目都未取货
            suggestion["order_item_id"] = item.id
            
            all_suggestions.append(suggestion)
    
    return all_suggestions

def get_expired_inventory(db: Session):
    """获取已过期的库存"""
    today = datetime.datetime.now().date()
    return db.query(models.Inventory)\
        .filter(
            models.Inventory.remaining > 0,
            models.Inventory.expiry_date < today
        )\
        .order_by(models.Inventory.expiry_date)\
        .all()

def get_near_expiry_inventory(db: Session, days=NEAR_EXPIRY_DAYS):
    """获取接近过期的库存"""
    today = datetime.datetime.now().date()
    future = today + datetime.timedelta(days=days)
    return db.query(models.Inventory)\
        .filter(
            models.Inventory.remaining > 0,
            models.Inventory.expiry_date >= today,
            models.Inventory.expiry_date <= future
        )\
        .order_by(models.Inventory.expiry_date)\
        .all()
