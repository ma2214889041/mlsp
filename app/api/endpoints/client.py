from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ...core.deps import get_db, get_current_restaurant_or_none, redirect_with_prefix
from ...core.config import get_url, BASE_PATH
from ...services.client_service import RestaurantService, OrderService, ProductService
from ...db import models

router = APIRouter()

# 设置模板
templates = Jinja2Templates(directory="/home/mlsp/app/templates")
templates.env.globals["root_path"] = BASE_PATH  # 添加全局变量
templates.env.globals["url_for"] = get_url  # 添加URL辅助函数

# 客户端首页
@router.get("/", response_class=HTMLResponse)
async def client_home(request: Request, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    products_list = product_service.get_available_products()
    return templates.TemplateResponse("client/index.html", {"request": request, "products": products_list})

# 客户登录页面
@router.get("/login", response_class=HTMLResponse)
async def client_login(request: Request):
    return templates.TemplateResponse("client/login.html", {"request": request})

# 客户登录处理
@router.post("/login")
async def client_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    restaurant_service = RestaurantService(db)
    restaurant = restaurant_service.authenticate(username, password)
    
    if not restaurant:
        return templates.TemplateResponse(
            "client/login.html", 
            {"request": request, "error": "用户名或密码错误"}
        )
    
    # 返回带有认证cookie的响应
    response = redirect_with_prefix("/client/dashboard")
    response.set_cookie(key="restaurant_id", value=str(restaurant.id))
    response.set_cookie(key="restaurant_name", value=restaurant.name)
    return response

# 客户注册页面
@router.get("/register", response_class=HTMLResponse)
async def client_register(request: Request):
    return templates.TemplateResponse("client/register.html", {"request": request})

# 客户注册处理
@router.post("/register")
async def client_register_post(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    restaurant_service = RestaurantService(db)
    
    # 检查用户名是否已存在
    if restaurant_service.get_restaurant_by_username(username):
        return templates.TemplateResponse(
            "client/register.html", 
            {"request": request, "error": "用户名已被使用"}
        )
    
    # 创建新餐馆用户
    new_restaurant = restaurant_service.create_restaurant(
        name=name, address=address, phone=phone, username=username, password=password
    )
    
    # 设置cookie并重定向
    response = redirect_with_prefix("/client/dashboard")
    response.set_cookie(key="restaurant_id", value=str(new_restaurant.id))
    response.set_cookie(key="restaurant_name", value=new_restaurant.name)
    return response

# 客户面板
@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(
    request: Request, 
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    restaurant_name = request.cookies.get("restaurant_name", "用户")
    return templates.TemplateResponse(
        "client/dashboard.html", 
        {"request": request, "restaurant_name": restaurant_name}
    )

# 客户产品列表
@router.get("/products", response_class=HTMLResponse)
async def client_products(
    request: Request, 
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    product_service = ProductService(db)
    products_list = product_service.get_products(active_only=True)
    return templates.TemplateResponse(
        "client/products.html", 
        {"request": request, "products": products_list}
    )

# 客户订单列表
@router.get("/orders", response_class=HTMLResponse)
async def client_orders(
    request: Request, 
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    restaurant_service = RestaurantService(db)
    orders_list = restaurant_service.get_restaurant_orders(int(restaurant_id))
    return templates.TemplateResponse(
        "client/orders.html", 
        {"request": request, "orders": orders_list}
    )

# 客户订单详情
@router.get("/order/{order_id}", response_class=HTMLResponse)
async def client_order_detail(
    request: Request, 
    order_id: int, 
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    order_service = OrderService(db)
    order_obj = order_service.get_order_for_restaurant(order_id, int(restaurant_id))
    
    if not order_obj:
        return templates.TemplateResponse(
            "client/order_detail.html", 
            {"request": request, "order": None, "items": []}
        )
    
    order_items = order_service.get_order_items(order_id)
    
    return templates.TemplateResponse(
        "client/order_detail.html", 
        {"request": request, "order": order_obj, "items": order_items}
    )

# 客户取消订单
@router.post("/order/{order_id}/cancel")
async def client_cancel_order(
    request: Request,
    order_id: int,
    cancel_reason: str = Form(...),
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    order_service = OrderService(db)
    order_obj = order_service.get_order_for_restaurant(order_id, int(restaurant_id))
    
    if not order_obj or order_obj.status != "pending":
        raise HTTPException(status_code=404, detail="订单不存在或无法取消")
    
    order_service.cancel_order(order_id, cancel_reason)
    return redirect_with_prefix(f"/client/order/{order_id}")

# 获取产品API
@router.get("/api/product/{product_id}")
async def get_product_info(
    product_id: int,
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    # 添加错误处理，防止'undefined'值导致的错误
    if isinstance(product_id, str) and product_id.lower() == "undefined":
        return JSONResponse(
            status_code=400,
            content={"error": "无效的产品ID"}
        )
        
    if not restaurant_id:
        return JSONResponse(
            status_code=401,
            content={"error": "未登录"}
        )
    
    try:
        product_service = ProductService(db)
        product = product_service.get_product(product_id)
        if not product:
            return JSONResponse(
                status_code=404,
                content={"error": "产品不存在"}
            )
        
        # 处理图片URL前缀，确保不会重复添加前缀
        image_url = product.image_url
        if image_url:
            image_url = get_url(image_url)
        
        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "image": image_url,
            "stock": product.stock,
            "unit_type": product.unit_type
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取产品信息出错: {str(e)}"}
        )

# 客户提交订单页面
@router.get("/create-order", response_class=HTMLResponse)
async def client_create_order(
    request: Request, 
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    product_service = ProductService(db)
    products_list = product_service.get_available_products()
    
    return templates.TemplateResponse(
        "client/create_order.html", 
        {"request": request, "products": products_list}
    )

# 客户提交订单
@router.post("/create-order")
async def client_submit_order(
    request: Request,
    items: str = Form(...),  # 格式: "product_id:quantity,product_id:quantity"
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    try:
        # 创建服务
        order_service = OrderService(db)
        product_service = ProductService(db)
        
        # 创建订单
        new_order = order_service.create_order(int(restaurant_id), note)
        
        # 解析订单项
        total_amount = 0
        
        for item in items.split(','):
            if not item:
                continue
            
            try:
                product_id, quantity = item.split(':')
                product_id = int(product_id)
                quantity = int(quantity)
            except ValueError as e:
                # 如果出错，删除已创建的订单
                db.delete(new_order)
                db.commit()
                return JSONResponse(
                    status_code=400,
                    content={"error": f"订单格式错误: {str(e)}"}
                )
            
            # 获取产品信息
            prod = product_service.get_product(product_id)
            if not prod or prod.stock < quantity:
                # 如果出错，删除已创建的订单
                db.delete(new_order)
                db.commit()
                
                return JSONResponse(
                    status_code=400,
                    content={"error": f"产品 {prod.name if prod else 'unknown'} 库存不足"}
                )
            
            # 添加订单项
            order_service.add_order_item(
                new_order.id, 
                product_id, 
                quantity, 
                prod.price, 
                prod.unit_type
            )
            
            # 更新产品库存
            product_service.update_product_stock(product_id, prod.stock - quantity)
            
            # 计算总金额
            total_amount += prod.price * quantity
        
        # 更新订单总金额
        order_service.update_order_total(new_order.id)
        
        return redirect_with_prefix(f"/client/order/{new_order.id}")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"创建订单出错: {str(e)}"}
        )

# 添加AI订单识别页面路由
@router.get("/order-recognition", response_class=HTMLResponse)
async def client_order_recognition(
    request: Request,
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return redirect_with_prefix("/client/login")
    
    return templates.TemplateResponse(
        "client/order_recognition.html", 
        {"request": request}
    )
