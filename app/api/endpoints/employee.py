from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import datetime
import urllib.parse
import shutil
import os
from pathlib import Path
import logging
import uuid

from ...core.deps import get_db, get_current_employee
from ...db import models
from ...crud import employee as employee_crud
from ...crud import order, inventory, product as product_crud

router = APIRouter()

# 设置模板
templates = Jinja2Templates(directory="/home/mlsp/app/templates")



# 创建日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("employee_api")

# 员工登录页面
@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
async def employee_login(request: Request):
    return templates.TemplateResponse("employee/login.html", {"request": request})

# 员工登录处理
@router.post("/login")
async def employee_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 使用数据库验证
    employee = employee_crud.authenticate_employee(db, username, password)
    
    if not employee:
        return templates.TemplateResponse(
            "employee/login.html", 
            {"request": request, "error": "用户名或密码错误，或账户已被禁用"}
        )
    
    # 返回带有认证cookie的响应
    response = RedirectResponse(url="/employee/dashboard", status_code=303)
    response.set_cookie(key="employee_authenticated", value="true")
    response.set_cookie(key="employee_id", value=str(employee.id))
    
    # 使用URL编码存储员工名称
    encoded_name = urllib.parse.quote(employee.name)
    response.set_cookie(key="employee_name", value=encoded_name)
    
    return response

# 员工仪表板
@router.get("/dashboard", response_class=HTMLResponse)
async def employee_dashboard(request: Request, db: Session = Depends(get_db)):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return RedirectResponse(url="/employee/login")
    
    # 获取待处理的已确认订单
    pending_orders = db.query(models.Order).filter(
        models.Order.status == "confirmed"
    ).order_by(models.Order.confirmed_at.desc()).all()
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    # 获取即将过期的商品列表（30天内）
    today = datetime.datetime.now().date()
    thirty_days_later = today + datetime.timedelta(days=30)
    
    expiry_alerts = db.query(models.Inventory).filter(
        models.Inventory.remaining > 0,
        models.Inventory.expiry_date > today,
        models.Inventory.expiry_date <= thirty_days_later
    ).order_by(models.Inventory.expiry_date).limit(10).all()
    
    return templates.TemplateResponse(
        "employee/dashboard.html", 
        {
            "request": request, 
            "orders": pending_orders, 
            "employee_name": employee_name,
            "expiry_alerts": expiry_alerts,
            "now": datetime.datetime.now()
        }
    )

# 扫描二维码页面
@router.get("/scan", response_class=HTMLResponse)
async def employee_scan_page(request: Request):
    """扫描二维码页面"""
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return RedirectResponse(url="/employee/login")
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    return templates.TemplateResponse(
        "employee/scan.html", 
        {"request": request, "employee_name": employee_name}
    )

# 验证订单二维码 - 修改此函数，降低权限验证要求
@router.post("/verify-order/{order_id}")
async def verify_order(
    order_id: int,
    request: Request, 
    db: Session = Depends(get_db)
):
    """验证订单二维码"""
    logger.info(f"验证订单 ID: {order_id}")
    
    # 检查认证 - 放宽要求，只要有cookie就可以
    if not request.cookies.get("employee_authenticated"):
        logger.error("未授权：缺少employee_authenticated cookie")
        return {"success": False, "message": "未授权，请先登录"}
    
    # 查找订单
    order_obj = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order_obj:
        logger.error(f"订单 {order_id} 不存在")
        return {"success": False, "message": "订单不存在"}
    
    # 检查订单状态
    if order_obj.status != "confirmed":
        logger.error(f"订单状态不正确，当前状态: {order_obj.status}")
        return {"success": False, "message": f"订单状态不正确，当前状态: {order_obj.status}"}
    
    # 成功，返回订单详情URL
    logger.info(f"订单 {order_id} 验证成功，重定向到订单详情页")
    return {"success": True, "redirect_url": f"/employee/order/{order_id}"}

# 验证货架二维码
@router.post("/verify-shelf/{shelf_id}")
async def verify_shelf(
    shelf_id: int,
    request: Request, 
    order_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """验证货架二维码"""
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return {"success": False, "message": "未授权"}
    
    # 查找货架
    shelf = db.query(models.Shelf).filter(models.Shelf.id == shelf_id).first()
    if not shelf:
        return {"success": False, "message": "货架不存在"}
    
    return {"success": True, "shelf_name": shelf.name, "shelf_location": shelf.location}

# 员工订单详情页面
@router.get("/order/{order_id}", response_class=HTMLResponse)
async def employee_order_detail(request: Request, order_id: int, db: Session = Depends(get_db)):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return RedirectResponse(url="/employee/login")
    
    # 获取订单详情
    order_obj = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order_obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 获取餐馆信息
    restaurant_obj = db.query(models.Restaurant).filter(
        models.Restaurant.id == order_obj.restaurant_id
    ).first()
    
    # 获取基于FIFO的库存取货建议
    inventory_suggestions = inventory.get_inventory_for_order(db, order_id)
    
    # 检查每个取货建议是否已经被取货过
    picking_records = db.query(models.PickingRecord).filter(
        models.PickingRecord.order_id == order_id
    ).all()
    
    # 标记已取货的项目
    picked_inventory_ids = [record.inventory_id for record in picking_records]
    for suggestion in inventory_suggestions:
        suggestion["picked"] = suggestion["inventory_id"] in picked_inventory_ids
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    return templates.TemplateResponse(
        "employee/order_detail.html", 
        {
            "request": request, 
            "order": order_obj, 
            "restaurant": restaurant_obj,
            "inventory_suggestions": inventory_suggestions,
            "employee_name": employee_name
        }
    )

# 标记订单项已取
@router.post("/order/{order_id}/item/{order_item_id}/pick")
async def employee_pick_item(
    request: Request, 
    order_id: int, 
    order_item_id: int, 
    inventory_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    logger.info(f"标记订单 {order_id} 的商品 {order_item_id} 为已取货，库存ID: {inventory_id}, 数量: {quantity}")
    
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        logger.error("未授权：缺少employee_authenticated cookie")
        return RedirectResponse(url="/employee/login")
    
    employee_id = request.cookies.get("employee_id")
    if not employee_id:
        logger.error("未找到员工ID")
        raise HTTPException(status_code=403, detail="未找到员工信息")
    
    try:
        # 更新库存剩余数量
        inventory.update_inventory_remaining(db, inventory_id, quantity)
        
        # 记录取货操作
        order.record_picking(db, order_id, inventory_id, int(employee_id), quantity)
        
        logger.info(f"成功标记订单 {order_id} 的商品 {order_item_id} 为已取货")
        return RedirectResponse(url=f"/employee/order/{order_id}", status_code=303)
    except Exception as e:
        logger.error(f"标记商品已取货时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"标记商品已取货时出错: {str(e)}")

# 上传订单照片
@router.post("/upload-order-photo")
async def upload_order_photo(
    request: Request, 
    photo: UploadFile = File(...),
    order_id: int = Form(...),
    db: Session = Depends(get_db)
):
    logger.info(f"上传订单 {order_id} 的照片")
    
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        logger.error("未授权：缺少employee_authenticated cookie")
        return JSONResponse(status_code=401, content={"success": False, "message": "未授权"})
    
    # 获取员工ID
    employee_id = request.cookies.get("employee_id")
    if not employee_id:
        logger.error("未找到员工ID")
        return JSONResponse(status_code=403, content={"success": False, "message": "未找到员工信息"})
    
    # 检查订单是否存在
    order_obj = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order_obj:
        logger.error(f"订单 {order_id} 不存在")
        return JSONResponse(status_code=404, content={"success": False, "message": "订单不存在"})
    
    try:
        # 创建保存照片的目录
        photos_dir = Path("/home/mlsp/app/static/uploads/order_photos")
        photos_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置目录权限
        os.system(f"chmod -R 777 {photos_dir}")
        
        # 生成唯一文件名，使用订单ID和时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"order_{order_id}_{timestamp}.jpg"
        file_path = photos_dir / filename
        
        # 保存照片
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        # 设置文件权限
        os.system(f"chmod 777 {file_path}")
        
        # 生成照片URL
        photo_url = f"/static/uploads/order_photos/{filename}"
        
        # 创建新的照片记录 - 修改此处允许一个订单有多张照片
        new_photo = models.OrderPhoto(
            order_id=order_id,
            photo_url=photo_url,
            uploaded_by=int(employee_id),
            uploaded_at=datetime.datetime.now()
        )
        db.add(new_photo)
        db.commit()
        
        logger.info(f"订单 {order_id} 照片上传成功，URL: {photo_url}")
        return JSONResponse(content={"success": True, "photo_url": photo_url})
    
    except Exception as e:
        logger.error(f"上传照片时出错: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"success": False, "message": f"上传照片时出错: {str(e)}"}
        )

# 完成订单
@router.post("/order/{order_id}/complete")
async def employee_complete_order(
    request: Request, 
    order_id: int, 
    photo_uploaded: str = Form("true"),  # 默认为true
    shelf_confirmed: str = Form("true"),  # 默认为true
    db: Session = Depends(get_db)
):
    logger.info(f"标记订单 {order_id} 为已完成")
    
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        logger.error("未授权：缺少employee_authenticated cookie")
        return RedirectResponse(url="/employee/login")
    
    # 检查是否已上传照片
    photos = db.query(models.OrderPhoto).filter(models.OrderPhoto.order_id == order_id).first()
    if not photos and photo_uploaded != "skip":
        logger.error(f"订单 {order_id} 未上传照片，无法完成")
        return RedirectResponse(url=f"/employee/order/{order_id}?error=no_photo", status_code=303)
    
    try:
        # 完成订单
        order.complete_order(db, order_id)
        logger.info(f"订单 {order_id} 已标记为完成")
        return RedirectResponse(url="/employee/dashboard", status_code=303)
    except Exception as e:
        logger.error(f"完成订单时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"完成订单时出错: {str(e)}")

# 新增 - 库存管理页面
@router.get("/inventory", response_class=HTMLResponse)
async def employee_inventory(request: Request, db: Session = Depends(get_db)):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return RedirectResponse(url="/employee/login")
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    # 获取所有货架
    shelves = db.query(models.Shelf).all()
    
    # 获取最近的入库记录
    recent_activities = db.query(models.Inventory).order_by(
        models.Inventory.entry_date.desc()
    ).limit(10).all()
    
    return templates.TemplateResponse(
        "employee/inventory.html", 
        {
            "request": request, 
            "employee_name": employee_name,
            "shelves": shelves,
            "recent_activities": recent_activities
        }
    )

# 新增 - 添加库存
@router.post("/inventory/add")
async def employee_add_inventory(
    request: Request, 
    product_id: int = Form(...),
    add_stock: int = Form(...),
    shelf_id: Optional[str] = Form(None),
    slot_id: Optional[str] = Form(None),
    expiry_date: str = Form(...),
    batch_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return RedirectResponse(url="/employee/login")
    
    try:
        # 获取产品信息
        product_obj = product_crud.get_product(db, product_id)
        if not product_obj:
            return RedirectResponse(url="/employee/inventory?error=product_not_found", status_code=303)
        
        # 处理空的slot_id
        slot_id_int = None
        if slot_id and slot_id.strip() and slot_id != "None" and slot_id != "null":
            try:
                slot_id_int = int(slot_id)
            except ValueError:
                slot_id_int = None
        
        # 生成批次号
        if not batch_number:
            batch_number = f"B{uuid.uuid4().hex[:8].upper()}"
        
        # 解析过期日期
        try:
            expiry_date_obj = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            # 使用默认过期日期（当前日期 + 产品的默认保质期）
            expiry_days = product_obj.expiry_days if product_obj and product_obj.expiry_days else 180
            expiry_date_obj = datetime.datetime.now().date() + datetime.timedelta(days=expiry_days)
        
        # 创建库存记录
        inventory.create_inventory(
            db, 
            product_id=product_id, 
            slot_id=slot_id_int, 
            quantity=add_stock, 
            unit_type=product_obj.unit_type,
            expiry_date=expiry_date_obj,
            batch_number=batch_number
        )
        
        return RedirectResponse(url="/employee/inventory?success=true", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/employee/inventory?error={str(e)}", status_code=303)

# 新增 - 获取产品API
@router.get("/api/product/{product_id}")
async def employee_get_product(
    product_id: int,
    request: Request, 
    db: Session = Depends(get_db)
):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return JSONResponse(status_code=401, content={"success": False, "message": "未授权"})
    
    # 获取产品信息
    product_obj = product_crud.get_product(db, product_id)
    if not product_obj:
        return JSONResponse(status_code=404, content={"success": False, "message": "产品不存在"})
    
    # 返回产品信息
    return {
        "success": True,
        "product": {
            "id": product_obj.id,
            "name": product_obj.name,
            "description": product_obj.description,
            "price": product_obj.price,
            "stock": product_obj.stock,
            "image_url": product_obj.image_url,
            "unit_type": product_obj.unit_type,
            "expiry_days": product_obj.expiry_days
        }
    }
