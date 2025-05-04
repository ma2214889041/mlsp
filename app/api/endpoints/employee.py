from fastapi import APIRouter, Request, Depends, Form, HTTPException, File, UploadFile, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import datetime
import urllib.parse
import logging

from ...core.deps import get_db, get_current_employee, redirect_with_prefix
from ...core.config import get_url, BASE_PATH
from ...services.employee_service import EmployeeService
from ...services.inventory_service import InventoryService
from ...db import models

router = APIRouter()

# 设置模板
templates = Jinja2Templates(directory="/home/mlsp/app/templates")
templates.env.globals["root_path"] = BASE_PATH  # 添加全局变量
templates.env.globals["url_for"] = get_url  # 添加URL辅助函数

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
    # 使用服务验证
    employee_service = EmployeeService(db)
    employee = employee_service.authenticate(username, password)
    
    if not employee:
        return templates.TemplateResponse(
            "employee/login.html", 
            {"request": request, "error": "用户名或密码错误，或账户已被禁用"}
        )
    
    # 返回带有认证cookie的响应
    response = redirect_with_prefix("/employee/dashboard")
    response.set_cookie(key="employee_authenticated", value="true")
    response.set_cookie(key="employee_id", value=str(employee.id))
    
    # 使用URL编码存储员工名称
    encoded_name = urllib.parse.quote(employee.name)
    response.set_cookie(key="employee_name", value=encoded_name)
    
    return response

# 员工仪表板
@router.get("/dashboard", response_class=HTMLResponse)
async def employee_dashboard(
    request: Request, 
    db: Session = Depends(get_db)
):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return redirect_with_prefix("/employee/login")
    
    # 创建服务
    employee_service = EmployeeService(db)
    
    # 获取待处理订单
    pending_orders = employee_service.get_pending_orders()
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    # 获取即将过期的警告
    expiry_alerts = employee_service.get_expiry_alerts()
    
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
        return redirect_with_prefix("/employee/login")
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    return templates.TemplateResponse(
        "employee/scan.html", 
        {"request": request, "employee_name": employee_name}
    )

# 验证订单二维码
@router.post("/verify-order/{order_id}")
async def verify_order(
    order_id: int,
    request: Request, 
    db: Session = Depends(get_db)
):
    """验证订单二维码"""
    logger.info(f"验证订单 ID: {order_id}")
    
    # 检查认证
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
    return {"success": True, "redirect_url": get_url(f"/employee/order/{order_id}")}

# 员工订单详情页面
@router.get("/order/{order_id}", response_class=HTMLResponse)
async def employee_order_detail(
    request: Request, 
    order_id: int, 
    db: Session = Depends(get_db)
):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return redirect_with_prefix("/employee/login")
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    # 获取订单详情
    order_obj = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order_obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 获取餐馆信息
    restaurant_obj = order_obj.restaurant
    
    # 获取库存取货建议
    inventory_service = InventoryService(db)
    inventory_suggestions = inventory_service.get_inventory_for_order(order_id)
    
    # 查找已取货记录
    picking_records = db.query(models.PickingRecord).filter(
        models.PickingRecord.order_id == order_id
    ).all()
    
    # 标记已取货的项目
    picked_inventory_ids = [record.inventory_id for record in picking_records]
    for suggestion in inventory_suggestions:
        suggestion["picked"] = suggestion["inventory_id"] in picked_inventory_ids
    
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
        return redirect_with_prefix("/employee/login")
    
    employee_id = request.cookies.get("employee_id")
    if not employee_id:
        logger.error("未找到员工ID")
        raise HTTPException(status_code=403, detail="未找到员工信息")
    
    try:
        # 记录取货
        employee_service = EmployeeService(db)
        result = employee_service.record_picking(order_id, inventory_id, int(employee_id), quantity)
        
        if not result:
            logger.error(f"取货失败：库存不足 (库存ID: {inventory_id}, 数量: {quantity})")
            raise HTTPException(status_code=400, detail="库存不足")
        
        logger.info(f"成功标记订单 {order_id} 的商品 {order_item_id} 为已取货")
        return redirect_with_prefix(f"/employee/order/{order_id}")
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
    
    try:
        employee_service = EmployeeService(db)
        photo_url = employee_service.upload_order_photo(order_id, int(employee_id), photo)
        
        if not photo_url:
            logger.error(f"上传照片失败：订单 {order_id} 不存在")
            return JSONResponse(status_code=404, content={"success": False, "message": "订单不存在"})
        
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
        return redirect_with_prefix("/employee/login")
    
    try:
        # 检查是否已上传照片
        employee_service = EmployeeService(db)
        if not employee_service.check_order_photos(order_id) and photo_uploaded != "skip":
            logger.error(f"订单 {order_id} 未上传照片，无法完成")
            return redirect_with_prefix(f"/employee/order/{order_id}?error=no_photo")
        
        # 完成订单
        order = employee_service.complete_order(order_id)
        if not order:
            logger.error(f"订单 {order_id} 不存在或状态不正确")
            raise HTTPException(status_code=404, detail="订单不存在或状态不正确")
        
        logger.info(f"订单 {order_id} 已标记为完成")
        return redirect_with_prefix("/employee/dashboard")
    except Exception as e:
        logger.error(f"完成订单时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"完成订单时出错: {str(e)}")

# 库存管理页面
@router.get("/inventory", response_class=HTMLResponse)
async def employee_inventory(request: Request, db: Session = Depends(get_db)):
    # 检查认证
    if request.cookies.get("employee_authenticated") != "true":
        return redirect_with_prefix("/employee/login")
    
    # 解码员工名称
    encoded_name = request.cookies.get("employee_name", "")
    employee_name = urllib.parse.unquote(encoded_name) if encoded_name else "员工"
    
    # 获取所有货架
    inventory_service = InventoryService(db)
    shelves = inventory_service.get_shelves()
    
    # 获取最近的入库记录
    employee_service = EmployeeService(db)
    recent_activities = employee_service.get_recent_inventory_activities()
    
    return templates.TemplateResponse(
        "employee/inventory.html", 
        {
            "request": request, 
            "employee_name": employee_name,
            "shelves": shelves,
            "recent_activities": recent_activities
        }
    )

# 添加库存
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
        return redirect_with_prefix("/employee/login")
    
    try:
        # 处理空的slot_id
        slot_id_int = None
        if slot_id and slot_id.strip() and slot_id != "None" and slot_id != "null":
            try:
                slot_id_int = int(slot_id)
            except ValueError:
                slot_id_int = None
        
        # 解析过期日期
        try:
            expiry_date_obj = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            # 使用默认过期日期
            product = db.query(models.Product).filter(models.Product.id == product_id).first()
            expiry_days = product.expiry_days if product and product.expiry_days else 180
            expiry_date_obj = datetime.datetime.now().date() + datetime.timedelta(days=expiry_days)
        
        # 添加库存
        employee_service = EmployeeService(db)
        inventory = employee_service.add_inventory(
            product_id=product_id,
            quantity=add_stock,
            expiry_date=expiry_date_obj,
            slot_id=slot_id_int,
            batch_number=batch_number
        )
        
        if not inventory:
            return redirect_with_prefix("/employee/inventory?error=product_not_found")
        
        return redirect_with_prefix("/employee/inventory?success=true")
    except Exception as e:
        return redirect_with_prefix(f"/employee/inventory?error={str(e)}")

# 获取产品API
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
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"success": False, "message": "产品不存在"})
    
    # 返回产品信息
    return {
        "success": True,
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "image_url": get_url(product.image_url) if product.image_url else None,
            "unit_type": product.unit_type,
            "expiry_days": product.expiry_days
        }
    }
