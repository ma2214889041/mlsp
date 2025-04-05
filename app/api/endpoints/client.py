from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from ...core.deps import get_db, get_current_restaurant_or_none
from ...crud import product, order, restaurant
from ...db import models

router = APIRouter()

# 设置模板
templates = Jinja2Templates(directory="/home/mlsp/app/templates")
templates.env.globals["root_path"] = "/mlsp"  # 添加全局变量

# 客户端首页
@router.get("/", response_class=HTMLResponse)
async def client_home(request: Request, db: Session = Depends(get_db)):
    products_list = product.get_available_products(db)
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
    auth_result = restaurant.authenticate_restaurant(db, username, password)
    
    if not auth_result:
        return templates.TemplateResponse(
            "client/login.html", 
            {"request": request, "error": "用户名或密码错误"}
        )
    
    # 返回带有认证cookie的响应
    response = RedirectResponse(url="/mlsp/client/dashboard", status_code=303)
    response.set_cookie(key="restaurant_id", value=str(auth_result.id))
    response.set_cookie(key="restaurant_name", value=auth_result.name)
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
    # 检查用户名是否已存在
    existing_user = restaurant.get_restaurant_by_username(db, username)
    if existing_user:
        return templates.TemplateResponse(
            "client/register.html", 
            {"request": request, "error": "用户名已被使用"}
        )
    
    # 创建新餐馆用户
    new_restaurant = restaurant.create_restaurant(
        db, name=name, address=address, phone=phone, username=username, password=password
    )
    
    # 设置cookie并重定向
    response = RedirectResponse(url="/mlsp/client/dashboard", status_code=303)
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
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
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
    products_list = product.get_products(db, active_only=True)
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
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    orders_list = order.get_orders(db, restaurant_id=int(restaurant_id))
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
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    order_obj = order.get_order_with_restaurant(db, order_id, int(restaurant_id))
    
    if not order_obj:
        return templates.TemplateResponse(
            "client/order_detail.html", 
            {"request": request, "order": None, "items": []}
        )
    
    order_items = order.get_order_items(db, order_id)
    
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
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    order_obj = order.get_order_with_restaurant(db, order_id, int(restaurant_id))
    
    if not order_obj or order_obj.status != "pending":
        raise HTTPException(status_code=404, detail="订单不存在或无法取消")
    
    order.cancel_order(db, order_id, cancel_reason)
    return RedirectResponse(url=f"/mlsp/client/order/{order_id}", status_code=303)

# 客户修改订单页面
@router.get("/order/{order_id}/edit", response_class=HTMLResponse)
async def client_edit_order(
    request: Request, 
    order_id: int, 
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    order_obj = order.get_order_with_restaurant(db, order_id, int(restaurant_id))
    
    if not order_obj or order_obj.status != "pending":
        raise HTTPException(status_code=404, detail="订单不存在或无法修改")
    
    order_items = order.get_order_items(db, order_id)
    products_list = product.get_products(db, active_only=True)
    
    return templates.TemplateResponse(
        "client/edit_order.html", 
        {"request": request, "order": order_obj, "items": order_items, "products": products_list}
    )

# 客户更新订单
@router.post("/order/{order_id}/update")
async def client_update_order(
    request: Request,
    order_id: int,
    items: str = Form(...),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    order_obj = order.get_order_with_restaurant(db, order_id, int(restaurant_id))
    
    if not order_obj or order_obj.status != "pending":
        raise HTTPException(status_code=404, detail="订单不存在或无法修改")
    
    # 恢复原订单库存
    order_items = order.get_order_items(db, order_id)
    for item in order_items:
        prod = product.get_product(db, item.product_id)
        if prod:
            product.update_product(db, prod.id, stock=prod.stock + item.quantity)
    
    # 删除原订单项
    db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).delete()
    
    # 解析新订单项
    item_list = []
    total_amount = 0
    
    for item in items.split(','):
        if not item:
            continue
        
        product_id, quantity = item.split(':')
        product_id = int(product_id)
        quantity = int(quantity)
        
        # 获取产品信息
        prod = product.get_product(db, product_id)
        if not prod or prod.stock < quantity:
            return JSONResponse(
                status_code=400,
                content={"error": f"产品 {prod.name if prod else 'unknown'} 库存不足"}
            )
        
        item_list.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": prod.price,
            "unit_type": prod.unit_type
        })
        
        # 更新库存
        product.update_product(db, prod.id, stock=prod.stock - quantity)
        
        # 计算总金额
        total_amount += prod.price * quantity
    
    # 更新订单
    order.update_order(db, order_id, {"total_amount": total_amount, "note": note})
    
    # 创建新订单项
    for item in item_list:
        order_item = models.OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            unit_type=item["unit_type"]
        )
        db.add(order_item)
    
    db.commit()
    
    return RedirectResponse(url=f"/mlsp/client/order/{order_id}", status_code=303)

# 客户提交订单页面
@router.get("/create-order", response_class=HTMLResponse)
async def client_create_order(
    request: Request, 
    db: Session = Depends(get_db),
    restaurant_id: str = Depends(get_current_restaurant_or_none)
):
    if not restaurant_id:
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    products_list = product.get_available_products(db)
    
    return templates.TemplateResponse(
        "client/create_order.html", 
        {"request": request, "products": products_list}
    )

# 获取购物车中商品信息
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
        prod = product.get_product(db, product_id)
        if not prod:
            return JSONResponse(
                status_code=404,
                content={"error": "产品不存在"}
            )
        
        # 处理图片URL前缀
        image_url = prod.image_url
        if image_url and image_url.startswith('/') and not image_url.startswith('/mlsp'):
            image_url = f"/mlsp{image_url}"
        
        return {
            "id": prod.id,
            "name": prod.name,
            "price": prod.price,
            "image": image_url,
            "stock": prod.stock,
            "unit_type": prod.unit_type
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取产品信息出错: {str(e)}"}
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
        return RedirectResponse(url="/mlsp/client/login", status_code=303)
    
    try:
        # 创建订单
        new_order = order.create_order(db, int(restaurant_id), note)
        
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
                db.delete(new_order)
                db.commit()
                return JSONResponse(
                    status_code=400,
                    content={"error": f"订单格式错误: {str(e)}"}
                )
            
            # 获取产品信息
            prod = product.get_product(db, product_id)
            if not prod or prod.stock < quantity:
                # 如果出错，删除已创建的订单
                db.delete(new_order)
                db.commit()
                
                return JSONResponse(
                    status_code=400,
                    content={"error": f"产品 {prod.name if prod else 'unknown'} 库存不足"}
                )
            
            # 添加订单项
            order.add_order_item(
                db, 
                new_order.id, 
                product_id, 
                quantity, 
                prod.price, 
                prod.unit_type
            )
            
            # 更新产品库存
            product.update_product(db, prod.id, stock=prod.stock - quantity)
            
            # 计算总金额
            total_amount += prod.price * quantity
        
        # 更新订单总金额
        order.update_order_total(db, new_order.id)
        
        return RedirectResponse(url=f"/mlsp/client/order/{new_order.id}", status_code=303)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"创建订单出错: {str(e)}"}
        )
