from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
import shutil
import uuid
import re
from datetime import datetime

from ...core.deps import get_db, get_current_restaurant_or_none
from ...services.client_service import ProductService, OrderService
from ...db import models

router = APIRouter(prefix="/api/order-recognition", tags=["order-recognition-client"])

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_recognition_client")

# 用于存储会话状态的简单内存存储
active_sessions = {}

@router.post("/upload-photo")
async def upload_order_photo(
    request: Request,
    photo: UploadFile = File(...),
    restaurant_id: str = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """上传订单照片并进行识别"""
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    try:
        # 保存照片
        upload_dir = "/home/mlsp/app/static/uploads/order_photos"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"order_{restaurant_id}_{timestamp}.jpg"
        file_path = os.path.join(upload_dir, filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        # 设置权限
        os.chmod(file_path, 0o777)
        
        # 创建会话ID
        session_id = str(uuid.uuid4())
        
        # 模拟AI识别结果 - 在实际应用中这里应调用AI服务
        product_service = ProductService(db)
        products = product_service.get_available_products()
        
        # 随机选择1-3个产品作为识别结果
        import random
        sample_size = min(random.randint(1, 3), len(products))
        selected_products = random.sample(products, sample_size) if products else []
        
        products_result = []
        for product in selected_products:
            quantity = random.randint(1, 5)
            products_result.append({
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "quantity": quantity,
                "unit_type": product.unit_type or "份"
            })
        
        # 存储会话状态
        active_sessions[session_id] = {
            "restaurant_id": restaurant_id,
            "photo_path": file_path,
            "photo_url": f"/static/uploads/order_photos/{filename}",
            "products": products_result,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        logger.info(f"创建新会话: {session_id}, 产品数量: {len(products_result)}")
        
        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "photo_url": f"/static/uploads/order_photos/{filename}",
            "products": products_result,
            "message": "照片上传成功并已识别订单内容"
        })
    
    except Exception as e:
        logger.error(f"订单照片处理失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"订单照片处理失败: {str(e)}"}
        )

@router.post("/adjust-order")
async def adjust_order_via_chat(
    request: Request,
    session_id: str = Form(...),
    message: str = Form(...),
    restaurant_id: str = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """通过对话调整订单内容"""
    logger.info(f"调整订单: session_id={session_id}, message={message}")
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    # 检查会话是否存在
    if session_id not in active_sessions:
        logger.error(f"会话不存在: {session_id}")
        return JSONResponse(status_code=404, content={"success": False, "message": "会话不存在或已过期"})
    
    # 检查会话是否属于当前餐馆
    session = active_sessions[session_id]
    if session["restaurant_id"] != restaurant_id:
        return JSONResponse(status_code=403, content={"success": False, "message": "无权访问此会话"})
    
    try:
        # 获取当前产品列表
        products = session["products"]
        product_service = ProductService(db)
        all_products = product_service.get_available_products()
        
        # 提取数量 - 先找出数字
        quantity_match = re.search(r'\d+', message)
        quantity = int(quantity_match.group()) if quantity_match else 1
        
        logger.info(f"提取数量: {quantity}")
        
        # 提取产品名称 - 查找所有产品
        found_product = None
        for product in all_products:
            # 检查产品名称是否在消息中
            if product.name in message:
                found_product = product
                logger.info(f"找到产品: {product.name}")
                break
        
        # 调整订单逻辑
        if "添加" in message or "加" in message:
            if found_product:
                # 检查是否已存在
                existing = False
                for p in products:
                    if p["id"] == found_product.id:
                        p["quantity"] = quantity  # 设置为用户指定的数量
                        existing = True
                        break
                
                if not existing:
                    # 添加新商品
                    products.append({
                        "id": found_product.id,
                        "name": found_product.name,
                        "price": float(found_product.price),
                        "quantity": quantity,  # 使用提取的数量
                        "unit_type": found_product.unit_type or "份"
                    })
                
                response = f"已添加{quantity}{found_product.unit_type or '份'}{found_product.name}到订单"
                logger.info(response)
            else:
                # 尝试根据关键词查找产品
                keywords = message.replace("添加", "").replace("加", "").strip()
                if quantity_match:
                    # 移除数字部分
                    keywords = keywords.replace(quantity_match.group(), "").strip()
                
                logger.info(f"搜索关键词: '{keywords}'")
                
                if keywords:
                    matched_products = []
                    for product in all_products:
                        if keywords in product.name or product.name in keywords:
                            matched_products.append(product)
                    
                    if matched_products:
                        # 使用第一个匹配的产品
                        product = matched_products[0]
                        logger.info(f"通过关键词找到产品: {product.name}")
                        
                        # 检查是否已存在
                        existing = False
                        for p in products:
                            if p["id"] == product.id:
                                p["quantity"] = quantity  # 设置为用户指定的数量
                                existing = True
                                break
                        
                        if not existing:
                            # 添加新商品
                            products.append({
                                "id": product.id,
                                "name": product.name,
                                "price": float(product.price),
                                "quantity": quantity,
                                "unit_type": product.unit_type or "份"
                            })
                        
                        response = f"已添加{quantity}{product.unit_type or '份'}{product.name}到订单"
                        logger.info(response)
                    else:
                        response = f"抱歉，我没能找到「{keywords}」相关的产品。您可以尝试使用完整的产品名称。"
                else:
                    response = "抱歉，我没有理解您想添加什么产品。请指定产品名称。"
        
        elif "删除" in message or "去掉" in message or "移除" in message:
            if found_product:
                # 查找并删除
                for i, p in enumerate(products):
                    if p["id"] == found_product.id:
                        products.pop(i)
                        response = f"已从订单中删除{found_product.name}"
                        break
                else:
                    response = f"订单中没有{found_product.name}，无法删除"
            else:
                # 尝试根据关键词查找产品
                keywords = message.replace("删除", "").replace("去掉", "").replace("移除", "").strip()
                found = False
                
                for i, p in enumerate(products):
                    if keywords in p["name"] or p["name"] in keywords:
                        products.pop(i)
                        response = f"已从订单中删除{p['name']}"
                        found = True
                        break
                
                if not found:
                    response = f"订单中没有找到「{keywords}」相关的产品，无法删除"
        
        elif "改" in message or "修改" in message or "调整" in message:
            if found_product:
                # 查找并修改数量
                for p in products:
                    if p["id"] == found_product.id:
                        p["quantity"] = quantity
                        response = f"已将{found_product.name}的数量修改为{quantity}{p['unit_type']}"
                        break
                else:
                    # 如果订单中没有该产品，添加它
                    products.append({
                        "id": found_product.id,
                        "name": found_product.name,
                        "price": float(found_product.price),
                        "quantity": quantity,
                        "unit_type": found_product.unit_type or "份"
                    })
                    response = f"订单中没有{found_product.name}，已添加{quantity}{found_product.unit_type or '份'}"
            else:
                # 尝试根据关键词匹配
                modified = False
                keywords = message.replace("改", "").replace("修改", "").replace("调整", "").strip()
                if quantity_match:
                    # 移除数字部分
                    keywords = keywords.replace(quantity_match.group(), "").strip()
                
                for p in products:
                    if keywords in p["name"] or p["name"] in keywords:
                        p["quantity"] = quantity
                        response = f"已将{p['name']}的数量修改为{quantity}{p['unit_type']}"
                        modified = True
                        break
                
                if not modified:
                    response = f"订单中没有找到「{keywords}」相关的产品，无法修改数量"
        
        else:
            # 通用处理 - 尽可能理解用户意图
            if found_product:
                # 默认假设用户想要修改/添加产品
                existing = False
                for p in products:
                    if p["id"] == found_product.id:
                        p["quantity"] = quantity
                        response = f"已将{found_product.name}的数量更新为{quantity}{p['unit_type']}"
                        existing = True
                        break
                
                if not existing:
                    products.append({
                        "id": found_product.id,
                        "name": found_product.name,
                        "price": float(found_product.price),
                        "quantity": quantity,
                        "unit_type": found_product.unit_type or "份"
                    })
                    response = f"已添加{quantity}{found_product.unit_type or '份'}{found_product.name}到订单"
            else:
                response = "我不太确定您想做什么。您可以尝试说：添加5份牛肉、删除鸡肉或将牛肉改为3份。"
        
        # 更新会话状态
        session["products"] = products
        session["last_updated"] = datetime.now()
        active_sessions[session_id] = session
        
        logger.info(f"调整订单完成，当前产品数量: {len(products)}")
        
        return JSONResponse(content={
            "success": True,
            "response": response,
            "products": products  # 返回完整的产品列表以便前端更新
        })
    
    except Exception as e:
        logger.error(f"调整订单失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"调整订单失败: {str(e)}"}
        )

@router.post("/update-item-quantity")
async def update_item_quantity(
    request: Request,
    session_id: str = Form(...),
    product_id: int = Form(...),
    quantity: int = Form(...),
    restaurant_id: str = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """更新商品数量"""
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    # 检查会话是否存在
    if session_id not in active_sessions:
        return JSONResponse(status_code=404, content={"success": False, "message": "会话不存在或已过期"})
    
    # 检查会话是否属于当前餐馆
    session = active_sessions[session_id]
    if session["restaurant_id"] != restaurant_id:
        return JSONResponse(status_code=403, content={"success": False, "message": "无权访问此会话"})
    
    try:
        products = session["products"]
        product_service = ProductService(db)
        product = product_service.get_product(product_id)
        
        if not product:
            return JSONResponse(status_code=404, content={"success": False, "message": "产品不存在"})
        
        # 检查是否已存在该产品
        product_found = False
        for i, p in enumerate(products):
            if p["id"] == product_id:
                if quantity > 0:
                    products[i]["quantity"] = quantity
                    message = f"已将{product.name}的数量更新为{quantity}{product.unit_type or '份'}。"
                else:
                    products.pop(i)
                    message = f"已从订单中移除{product.name}。"
                product_found = True
                break
        
        # 如果产品不在列表中且数量大于0，则添加
        if not product_found and quantity > 0:
            products.append({
                "id": product_id,
                "name": product.name,
                "price": float(product.price),
                "quantity": quantity,
                "unit_type": product.unit_type or "份"
            })
            message = f"已添加{product.name} {quantity}{product.unit_type or '份'}到订单。"
        
        # 更新会话状态
        session["products"] = products
        session["last_updated"] = datetime.now()
        active_sessions[session_id] = session
        
        return JSONResponse(content={
            "success": True,
            "products": products,
            "message": message
        })
    
    except Exception as e:
        logger.error(f"更新商品数量失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新商品数量失败: {str(e)}"}
        )

@router.post("/voice-adjust-order")
async def voice_adjust_order(
    request: Request,
    session_id: str = Form(...),
    audio: UploadFile = File(...),
    restaurant_id: str = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """通过语音调整订单"""
    try:
        if not restaurant_id:
            return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
        
        # 检查会话是否存在
        if session_id not in active_sessions:
            return JSONResponse(status_code=404, content={"success": False, "message": "会话不存在或已过期"})
        
        # 检查会话是否属于当前餐馆
        session = active_sessions[session_id]
        if session["restaurant_id"] != restaurant_id:
            return JSONResponse(status_code=403, content={"success": False, "message": "无权访问此会话"})
        
        # 保存语音文件
        audio_content = await audio.read()
        
        # 模拟语音识别 - 在实际应用中会调用专门的API
        # 这里我们简单返回一个固定结果进行测试
        transcript = "添加5份牛肉"
        
        # 处理识别出的文本，调用adjust_order_via_chat的逻辑
        from fastapi.encoders import jsonable_encoder
        
        # 构造Form提交
        form_data = {
            "session_id": session_id,
            "message": transcript
        }
        
        # 调用调整订单的函数
        adjust_result = await adjust_order_via_chat(
            request=request,
            session_id=session_id,
            message=transcript,
            restaurant_id=restaurant_id,
            db=db
        )
        
        # 从结果中获取需要的数据
        result_content = jsonable_encoder(adjust_result)
        
        # 添加语音识别的文本
        result_content["transcript"] = transcript
        
        return JSONResponse(content=result_content)
    
    except Exception as e:
        logger.error(f"语音调整订单失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"语音调整订单失败: {str(e)}"}
        )

@router.post("/confirm-order")
async def confirm_order(
    request: Request,
    session_id: str = Form(...),
    note: Optional[str] = Form(None),
    restaurant_id: str = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """确认订单并提交到系统"""
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    # 检查会话是否存在
    if session_id not in active_sessions:
        return JSONResponse(status_code=404, content={"success": False, "message": "会话不存在或已过期"})
    
    # 检查会话是否属于当前餐馆
    session = active_sessions[session_id]
    if session["restaurant_id"] != restaurant_id:
        return JSONResponse(status_code=403, content={"success": False, "message": "无权访问此会话"})
    
    # 检查是否有订单项
    if not session["products"] or len(session["products"]) == 0:
        return JSONResponse(status_code=400, content={"success": False, "message": "订单中没有商品，无法提交"})
    
    try:
        order_service = OrderService(db)
        product_service = ProductService(db)
        
        # 创建订单
        new_order = order_service.create_order(int(restaurant_id), note)
        
        # 添加订单项
        total_amount = 0
        for item in session["products"]:
            product_id = item["id"]
            quantity = item["quantity"]
            unit_price = item["price"]
            unit_type = item["unit_type"]
            
            # 检查库存
            product = product_service.get_product(product_id)
            if not product or product.stock < quantity:
                # 回滚，删除订单
                db.delete(new_order)
                db.commit()
                
                error_msg = f"商品 {product.name if product else '未知'} 库存不足"
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": error_msg}
                )
            
            # 添加订单项
            order_service.add_order_item(
                new_order.id,
                product_id,
                quantity,
                unit_price,
                unit_type
            )
            
            # 更新产品库存
            product_service.update_product_stock(product_id, product.stock - quantity)
            
            # 计算总金额
            total_amount += unit_price * quantity
        
        # 更新订单总金额
        order_service.update_order(new_order.id, {"total_amount": total_amount})
        
        # 清理会话
        del active_sessions[session_id]
        
        return JSONResponse(content={
            "success": True,
            "order_id": new_order.id,
            "message": f"订单已成功提交，订单号: {new_order.id}",
            "redirect_url": f"/mlsp/client/order/{new_order.id}"
        })
    
    except Exception as e:
        logger.error(f"提交订单失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"提交订单失败: {str(e)}"}
        )

@router.get("/products/search")
async def search_products(
    request: Request,
    query: str,
    restaurant_id: str = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """搜索产品"""
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    try:
        product_service = ProductService(db)
        products = db.query(models.Product).filter(
            models.Product.name.contains(query),
            models.Product.is_active == True,
            models.Product.stock > 0
        ).limit(10).all()
        
        products_list = [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "stock": p.stock,
                "unit_type": p.unit_type or "份",
                "image_url": p.image_url
            }
            for p in products
        ]
        
        return JSONResponse(content={
            "success": True,
            "products": products_list
        })
    
    except Exception as e:
        logger.error(f"搜索产品失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"搜索产品失败: {str(e)}"}
        )
