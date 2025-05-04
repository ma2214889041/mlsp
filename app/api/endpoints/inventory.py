from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from ...core.deps import get_db, get_current_admin
from ...services.inventory_service import InventoryService
from ...db import models

router = APIRouter()

# 创建日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory_api")

# 获取所有货架
@router.get("/shelves")
async def get_all_shelves(
    db: Session = Depends(get_db)
):
    logger.info("获取所有货架")
    
    try:
        inventory_service = InventoryService(db)
        shelves = inventory_service.get_shelves()
        
        shelves_data = []
        for shelf in shelves:
            slots_count = len(shelf.slots) if shelf.slots else 0
            shelves_data.append({
                "id": shelf.id,
                "name": shelf.name,
                "location": shelf.location,
                "slots_count": slots_count
            })
        
        logger.info(f"找到 {len(shelves_data)} 个货架")
        return {"shelves": shelves_data}
    except Exception as e:
        logger.error(f"获取货架时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取货架失败: {str(e)}")

# 获取货架的所有货位
@router.get("/shelf/{shelf_id}/slots")
async def get_shelf_slots(
    shelf_id: int,
    db: Session = Depends(get_db)
):
    logger.info(f"获取货架 {shelf_id} 的所有货位")
    
    try:
        inventory_service = InventoryService(db)
        
        # 查询指定货架是否存在
        shelf = inventory_service.get_shelf(shelf_id)
        if not shelf:
            logger.error(f"货架 {shelf_id} 不存在")
            raise HTTPException(status_code=404, detail=f"货架 {shelf_id} 不存在")
        
        # 查询指定货架的所有货位
        slots = inventory_service.get_shelf_slots(shelf_id)
        
        # 格式化响应数据
        slots_data = []
        for slot in slots:
            # 检查是否有inventory属性
            has_inventory = False
            if hasattr(slot, 'inventories') and slot.inventories:
                has_inventory = any(inv.remaining > 0 for inv in slot.inventories)
            
            slots_data.append({
                "id": slot.id, 
                "position": slot.position,
                "is_occupied": has_inventory
            })
            
        logger.info(f"找到 {len(slots_data)} 个货位")
        
        return {"slots": slots_data}
    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        logger.error(f"获取货位时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取货位失败: {str(e)}")
