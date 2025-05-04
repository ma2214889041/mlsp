from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime

from ..db import models
from ..core.config import NEAR_EXPIRY_DAYS

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_shelves(self):
        """获取所有货架"""
        return self.db.query(models.Shelf).all()
    
    def get_shelf(self, shelf_id: int):
        """获取单个货架"""
        return self.db.query(models.Shelf).filter(models.Shelf.id == shelf_id).first()
    
    def get_shelf_slots(self, shelf_id: int):
        """获取货架上的所有货位"""
        return self.db.query(models.ShelfSlot).filter(models.ShelfSlot.shelf_id == shelf_id).all()
    
    def get_slot(self, slot_id: int):
        """获取单个货位"""
        return self.db.query(models.ShelfSlot).filter(models.ShelfSlot.id == slot_id).first()
    
    def create_shelf(self, name: str, location: str):
        """创建货架"""
        shelf = models.Shelf(
            name=name,
            location=location,
            created_at=datetime.datetime.now()
        )
        self.db.add(shelf)
        self.db.commit()
        self.db.refresh(shelf)
        return shelf
    
    def update_shelf(self, shelf_id: int, name: str, location: str):
        """更新货架信息"""
        shelf = self.get_shelf(shelf_id)
        if not shelf:
            return None
        
        shelf.name = name
        shelf.location = location
        self.db.commit()
        self.db.refresh(shelf)
        return shelf
    
    def delete_shelf(self, shelf_id: int):
        """删除货架"""
        shelf = self.get_shelf(shelf_id)
        if not shelf:
            return False
        
        self.db.delete(shelf)
        self.db.commit()
        return True
    
    def create_shelf_slot(self, shelf_id: int, position: str):
        """创建货位"""
        slot = models.ShelfSlot(
            shelf_id=shelf_id,
            position=position,
            created_at=datetime.datetime.now()
        )
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot
    
    def delete_shelf_slot(self, slot_id: int):
        """删除货位"""
        slot = self.get_slot(slot_id)
        if not slot:
            return False
        
        self.db.delete(slot)
        self.db.commit()
        return True
    
    def get_shelf_statistics(self):
        """获取货架统计信息"""
        total_shelves = self.db.query(models.Shelf).count()
        total_slots = self.db.query(models.ShelfSlot).count()
        
        # 通过查询有库存的货位数量
        occupied_slots_count = self.db.query(models.ShelfSlot).join(
            models.Inventory, 
            models.ShelfSlot.id == models.Inventory.slot_id
        ).distinct(models.ShelfSlot.id).count()
        
        return {
            "total_shelves": total_shelves,
            "total_slots": total_slots,
            "occupied_slots": occupied_slots_count,
            "empty_slots": total_slots - occupied_slots_count
        }
    
    def get_inventory_for_product(self, product_id: int, quantity: int):
        """按先进先出获取产品的取货建议"""
        # 查询产品的库存记录，按过期日期和入库日期排序
        inventory_items = self.db.query(models.Inventory).filter(
            models.Inventory.product_id == product_id,
            models.Inventory.remaining > 0
        ).order_by(
            models.Inventory.expiry_date, 
            models.Inventory.entry_date
        ).all()
        
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
    
    def get_inventory_for_order(self, order_id: int):
        """获取订单的所有库存取货建议"""
        order_items = self.db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
        
        all_suggestions = []
        
        for item in order_items:
            result = self.get_inventory_for_product(item.product_id, item.quantity)
            
            for suggestion in result["suggestions"]:
                # 添加产品信息
                product = self.db.query(models.Product).filter(models.Product.id == item.product_id).first()
                suggestion["product_id"] = item.product_id
                suggestion["product_name"] = product.name if product else "未知产品"
                suggestion["picked"] = False
                suggestion["order_item_id"] = item.id
                
                all_suggestions.append(suggestion)
        
        return all_suggestions
    
    def mark_items_picked(self, order_id: int):
        """检查订单的项目是否都已取货"""
        picking_records = self.db.query(models.PickingRecord).filter(
            models.PickingRecord.order_id == order_id
        ).all()
        
        order_items = self.db.query(models.OrderItem).filter(
            models.OrderItem.order_id == order_id
        ).all()
        
        # 检查每个订单项是否都有足够的取货记录
        for item in order_items:
            picked_quantity = 0
            
            for record in picking_records:
                inventory = self.db.query(models.Inventory).filter(
                    models.Inventory.id == record.inventory_id,
                    models.Inventory.product_id == item.product_id
                ).first()
                
                if inventory:
                    picked_quantity += record.quantity
            
            if picked_quantity < item.quantity:
                return False
        
        return True
