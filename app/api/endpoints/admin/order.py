from fastapi import APIRouter, Request, Depends, Path, Query, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from ....core.deps import get_db, get_current_admin
from ....db import models
from ....crud import order, inventory

router = APIRouter()
templates = Jinja2Templates(directory="/home/mlsp/app/templates")

@router.get("/{order_id}", response_class=HTMLResponse)
async def admin_view_order(
    request: Request,
    order_id: int = Path(...),
    db: Session = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    # 获取订单信息
    order_obj = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order_obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 获取订单项目
    order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
    
    # 获取餐馆信息
    restaurant_obj = db.query(models.Restaurant).filter(models.Restaurant.id == order_obj.restaurant_id).first()
    
    # 获取库存取货建议
    inventory_suggestions = []
    if order_obj.status == "confirmed":
        inventory_suggestions = inventory.get_inventory_for_order(db, order_id)
    
    # 传递数据库连接和模型到模板
    return templates.TemplateResponse(
        "admin/order_detail.html",
        {
            "request": request,
            "order": order_obj,
            "items": order_items,
            "restaurant": restaurant_obj,
            "inventory_suggestions": inventory_suggestions,
            "db": db,
            "models": models
        }
    )

@router.post("/{order_id}/confirm")
async def admin_confirm_order(
    request: Request,
    order_id: int = Path(...),
    pickup_time: str = Form(...),
    db: Session = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    # 确认订单
    order.confirm_order(db, order_id, pickup_time)
    return RedirectResponse(url=f"/admin/order/{order_id}", status_code=303)

@router.post("/{order_id}/complete")
async def admin_complete_order(
    request: Request,
    order_id: int = Path(...),
    db: Session = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    # 完成订单
    order.complete_order(db, order_id)
    return RedirectResponse(url=f"/admin/order/{order_id}", status_code=303)

@router.post("/{order_id}/cancel")
async def admin_cancel_order(
    request: Request,
    order_id: int = Path(...),
    cancel_reason: str = Form(...),
    db: Session = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    # 取消订单
    order.cancel_order(db, order_id, cancel_reason)
    return RedirectResponse(url=f"/admin/order/{order_id}", status_code=303)

@router.post("/{order_id}/set-pickup")
async def admin_set_pickup_time(
    request: Request,
    order_id: int = Path(...),
    pickup_time: str = Form(...),
    db: Session = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    # 更新取货时间
    order.update_pickup_time(db, order_id, pickup_time)
    return RedirectResponse(url=f"/admin/order/{order_id}", status_code=303)

@router.get("/{order_id}/picking", response_class=HTMLResponse)
async def admin_order_picking(
    request: Request,
    order_id: int = Path(...),
    db: Session = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    # 获取订单
    order_obj = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order_obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 获取餐馆信息
    restaurant_obj = order_obj.restaurant
    
    # 获取库存取货建议
    inventory_suggestions = inventory.get_inventory_for_order(db, order_id)
    
    return templates.TemplateResponse(
        "admin/picking.html",
        {
            "request": request,
            "order": order_obj,
            "restaurant": restaurant_obj,
            "inventory_suggestions": inventory_suggestions,
            "db": db,
            "models": models
        }
    )
