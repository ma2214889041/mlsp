from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from ...core.deps import get_db, get_current_admin, redirect_with_prefix
from ...core.config import get_url, BASE_PATH
from ...services.admin_service import AdminService
from ...services.inventory_service import InventoryService
from ...services.client_service import OrderService, ProductService
from ...services.employee_service import EmployeeService
from ...db import models

router = APIRouter()

# 设置模板
templates = Jinja2Templates(directory="/home/mlsp/app/templates")
templates.env.globals["root_path"] = BASE_PATH  # 添加全局变量
templates.env.globals["url_for"] = get_url  # 添加URL辅助函数

# 获取订单照片的辅助函数
def get_order_photos(order_id, db: Session):
    """获取特定订单的照片"""
    photos = db.query(models.OrderPhoto).filter(
        models.OrderPhoto.order_id == order_id
    ).order_by(models.OrderPhoto.uploaded_at.desc()).all()
    return photos

# 更新库存
@router.post("/inventory/update")
async def admin_update_inventory(
    request: Request,
    product_id: int = Form(...),
    add_stock: int = Form(...),
    shelf_id: Optional[str] = Form(None),
    slot_id: Optional[str] = Form(None),
    expiry_date: str = Form(...),  # YYYY-MM-DD格式
    batch_number: Optional[str] = Form(None),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
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
            product_service = ProductService(db)
            product = product_service.get_product(product_id)
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
            return redirect_with_prefix("/admin/inventory?error=product_not_found")
        
        return redirect_with_prefix("/admin/inventory")
    except Exception as e:
        return redirect_with_prefix(f"/admin/inventory?error={str(e)}")

# 管理员登录页面
@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})

# 管理员登录处理
@router.post("/login")
async def admin_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    if admin_service.authenticate(username, password):
        response = redirect_with_prefix("/admin/dashboard")
        response.set_cookie(key="admin_authenticated", value="true")
        return response
    else:
        return templates.TemplateResponse(
            "admin/login.html", 
            {"request": request, "error": "用户名或密码错误"}
        )

# 管理员仪表盘
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    stats = admin_service.get_dashboard_stats()
    
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {
            "request": request, 
            **stats  # 解包统计数据
        }
    )

# 管理员订单列表页面
@router.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request, 
    status: Optional[str] = None,
    restaurant_id: Optional[int] = None,
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    orders_list = admin_service.get_orders(status=status, restaurant_id=restaurant_id)
    
    return templates.TemplateResponse(
        "admin/orders.html", 
        {"request": request, "orders": orders_list, "current_status": status}
    )

# 管理员订单详情页面
@router.get("/order/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request, 
    order_id: int, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # 获取订单服务
    order_service = OrderService(db)
    inventory_service = InventoryService(db)
    
    # 获取订单
    order_obj = order_service.get_order(order_id)
    if not order_obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 获取订单项目
    order_items = order_service.get_order_items(order_id)
    
    # 获取库存取货建议
    inventory_suggestions = []
    if order_obj.status == "confirmed":
        inventory_suggestions = inventory_service.get_inventory_for_order(order_id)
    
    return templates.TemplateResponse(
        "admin/order_detail.html", 
        {
            "request": request, 
            "order": order_obj,
            "restaurant": order_obj.restaurant,
            "items": order_items,
            "inventory_suggestions": inventory_suggestions,
            "get_order_photos": get_order_photos,
            "db": db,
            "models": models
        }
    )

# 确认订单
@router.post("/order/{order_id}/confirm")
async def admin_confirm_order(
    request: Request,
    order_id: int,
    pickup_time: str = Form(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    order_service = OrderService(db)
    order_service.confirm_order(order_id, pickup_time)
    return redirect_with_prefix(f"/admin/order/{order_id}")

# 完成订单
@router.post("/order/{order_id}/complete")
async def admin_complete_order(
    request: Request,
    order_id: int,
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    order_service = OrderService(db)
    order_service.update_order(order_id, {"status": "completed", "completed_at": datetime.datetime.now()})
    return redirect_with_prefix(f"/admin/order/{order_id}")

# 取消订单
@router.post("/order/{order_id}/cancel")
async def admin_cancel_order(
    request: Request,
    order_id: int,
    cancel_reason: str = Form(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    order_service = OrderService(db)
    order_service.cancel_order(order_id, cancel_reason)
    return redirect_with_prefix(f"/admin/order/{order_id}")

# 设置取货时间
@router.post("/order/{order_id}/set-pickup")
async def admin_set_pickup_time(
    request: Request,
    order_id: int,
    pickup_time: str = Form(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    order_service = OrderService(db)
    order_service.update_order(order_id, {"pickup_time": pickup_time})
    return redirect_with_prefix(f"/admin/order/{order_id}")

# 管理员产品列表页面
@router.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    products_list = product_service.get_products()
    
    return templates.TemplateResponse(
        "admin/products.html", 
        {"request": request, "products": products_list}
    )

# 添加产品页面
@router.get("/product/add", response_class=HTMLResponse)
async def admin_add_product(
    request: Request, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    shelves = inventory_service.get_shelves()
    
    return templates.TemplateResponse(
        "admin/add_product.html", 
        {"request": request, "shelves": shelves}
    )

# 添加产品处理
@router.post("/product/add")
async def admin_add_product_post(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    expiry_days: int = Form(180),
    unit_type: str = Form("份"),
    shelf_id: Optional[str] = Form(None),
    image: UploadFile = File(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # 保存图片
    admin_service = AdminService(db)
    image_url = admin_service.save_product_image(image)
    
    # 创建产品
    product_service = ProductService(db)
    product = db.query(models.Product).filter(models.Product.name == name).first()
    
    if product:
        return redirect_with_prefix("/admin/products?error=product_exists")
    
    new_product = models.Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        image_url=image_url,
        unit_type=unit_type,
        expiry_days=expiry_days,
        is_active=True
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # 如果选择了货架，创建初始库存
    if shelf_id and stock > 0:
        employee_service = EmployeeService(db)
        
        # 解析货架ID
        slot_id_int = None
        if shelf_id.strip() and shelf_id != "None" and shelf_id != "null":
            try:
                slot_id_int = int(shelf_id)
            except ValueError:
                slot_id_int = None
                
        # 计算过期日期
        expiry_date = datetime.datetime.now().date() + datetime.timedelta(days=expiry_days)
        
        # 创建库存
        employee_service.add_inventory(
            product_id=new_product.id,
            quantity=stock,
            expiry_date=expiry_date,
            slot_id=slot_id_int
        )
    
    return redirect_with_prefix("/admin/products")

# 员工管理页面
@router.get("/employees", response_class=HTMLResponse)
async def admin_employees(
    request: Request, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    employees_list = admin_service.get_employees()
    
    return templates.TemplateResponse(
        "admin/employees.html", 
        {"request": request, "employees": employees_list}
    )

# 添加员工
@router.post("/employee/add")
async def admin_add_employee(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    position: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    is_active: bool = Form(False),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    employee = admin_service.create_employee(
        name=name,
        username=username,
        password=password,
        position=position,
        phone=phone,
        is_active=is_active
    )
    
    if not employee:
        return redirect_with_prefix("/admin/employees?error=username_exists")
    
    return redirect_with_prefix("/admin/employees")

# 编辑员工
@router.post("/employee/{employee_id}/edit")
async def admin_edit_employee(
    request: Request,
    employee_id: int,
    name: str = Form(...),
    username: str = Form(...),
    password: Optional[str] = Form(None),
    position: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    is_active: bool = Form(False),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    employee = admin_service.update_employee(
        employee_id=employee_id,
        name=name,
        username=username,
        password=password,
        position=position,
        phone=phone,
        is_active=is_active
    )
    
    if not employee:
        return redirect_with_prefix(f"/admin/employees?error=not_found&id={employee_id}")
    
    return redirect_with_prefix("/admin/employees")

# 删除员工
@router.post("/employee/{employee_id}/delete")
async def admin_delete_employee(
    request: Request,
    employee_id: int,
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    admin_service = AdminService(db)
    admin_service.delete_employee(employee_id)
    return redirect_with_prefix("/admin/employees")

# 管理员库存管理页面
@router.get("/inventory", response_class=HTMLResponse)
async def admin_inventory(
    request: Request, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    inventory_service = InventoryService(db)
    
    # 获取所有产品
    products_list = product_service.get_products()
    
    # 为每个产品处理图片URL前缀
    for prod in products_list:
        if prod.image_url:
            prod.image_url = get_url(prod.image_url)
    
    # 获取所有货架
    shelves = inventory_service.get_shelves()
    
    return templates.TemplateResponse(
        "admin/inventory.html", 
        {
            "request": request, 
            "products": products_list,
            "shelves": shelves,
            "now": datetime.datetime.now()
        }
    )

# 货架管理页面
@router.get("/shelves", response_class=HTMLResponse)
async def admin_shelves(
    request: Request, 
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    shelves_list = inventory_service.get_shelves()
    stats = inventory_service.get_shelf_statistics()
    
    # 为每个货架设置slot的过期状态
    for shelf in shelves_list:
        for slot in shelf.slots:
            if hasattr(slot, 'inventories') and slot.inventories:
                for inv in slot.inventories:
                    if inv.remaining > 0:
                        slot.is_expired = inv.is_expired()
                        slot.is_near_expiry = inv.is_near_expiry(30)
                        break
                else:
                    slot.is_expired = False
                    slot.is_near_expiry = False
            else:
                slot.is_expired = False
                slot.is_near_expiry = False
    
    return templates.TemplateResponse(
        "admin/shelves.html", 
        {
            "request": request, 
            "shelves": shelves_list,
            "total_slots": stats["total_slots"],
            "empty_slots": stats["empty_slots"]
        }
    )

# 添加货架
@router.post("/shelf/add")
async def admin_add_shelf(
    request: Request,
    name: str = Form(...),
    location: str = Form(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    inventory_service.create_shelf(name, location)
    return redirect_with_prefix("/admin/shelves")

# 编辑货架
@router.post("/shelf/{shelf_id}/edit")
async def admin_edit_shelf(
    request: Request,
    shelf_id: int,
    name: str = Form(...),
    location: str = Form(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    inventory_service.update_shelf(shelf_id, name, location)
    return redirect_with_prefix("/admin/shelves")

# 删除货架
@router.post("/shelf/{shelf_id}/delete")
async def admin_delete_shelf(
    request: Request,
    shelf_id: int,
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    inventory_service.delete_shelf(shelf_id)
    return redirect_with_prefix("/admin/shelves")

# 添加货位
@router.post("/shelf/{shelf_id}/add-slot")
async def admin_add_shelf_slot(
    request: Request,
    shelf_id: int,
    position: str = Form(...),
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    inventory_service.create_shelf_slot(shelf_id, position)
    return redirect_with_prefix("/admin/shelves")

# 删除货位
@router.post("/slot/{slot_id}/delete")
async def admin_delete_slot(
    request: Request,
    slot_id: int,
    is_admin: bool = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    inventory_service.delete_shelf_slot(slot_id)
    return redirect_with_prefix("/admin/shelves")
