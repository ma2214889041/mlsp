from fastapi import APIRouter, Request, Depends, File, UploadFile, Form, HTTPException, Body
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import shutil
import logging
import uuid
import json
import base64
from datetime import datetime
import random
import re

from ...core.deps import get_db, get_current_restaurant_or_none
from ...core.config import get_url
from ...services.client_service import ProductService, OrderService
from ...db import models

router = APIRouter(prefix="/api/order-recognition", tags=["order-recognition"])

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_recognition")

# 用于存储会话状态的简单内存存储
# 实际应用中应使用Redis等持久化方案
active_sessions = {}

# 存储语音回复的内存缓存
voice_responses = {}

@router.post("/upload-photo")
async def upload_order_photo(
    request: Request,
    photo: UploadFile = File(...),
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """上传订单照片并识别内容"""
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    try:
        # 保存照片
        file_path = await save_photo(photo)
        
        # 创建会话ID
        session_id = str(uuid.uuid4())
        
        # 使用AI识别照片中的订单内容
        recognition_result = await analyze_photo_with_ai(file_path, db)
        
        # 存储会话状态
        active_sessions[session_id] = {
            "restaurant_id": restaurant_id,
            "photo_path": file_path,
            "photo_url": get_url(f"/static/uploads/order_photos/{os.path.basename(file_path)}"),
            "recognized_items": recognition_result["items"],
            "original_text": recognition_result.get("original_text", ""),
            "chat_history": [
                {"role": "system", "content": "已识别订单内容，您可以通过对话调整订单项目。"}
            ],
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "photo_url": get_url(f"/static/uploads/order_photos/{os.path.basename(file_path)}"),
            "recognized_items": recognition_result["items"],
            "message": "照片上传成功并已识别订单内容"
        }
    
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
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """通过对话调整订单内容"""
    
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
        # 添加用户消息到历史记录
        session["chat_history"].append({"role": "user", "content": message})
        
        # 处理用户消息并调整订单
        adjustment_result = await process_adjustment(message, session, db)
        
        # 添加系统回复到历史记录
        session["chat_history"].append({"role": "system", "content": adjustment_result["response"]})
        
        # 更新会话状态
        session["recognized_items"] = adjustment_result["items"]
        session["last_updated"] = datetime.now()
        active_sessions[session_id] = session
        
        # 生成语音回复（如果环境变量启用语音）
        audio_url = None
        if os.environ.get("ENABLE_VOICE", "false").lower() == "true":
            try:
                from ...core.voice_service import BaiduVoiceService
                audio_data = await BaiduVoiceService.text_to_speech(adjustment_result["response"])
                voice_responses[session_id] = audio_data
                audio_url = f"/api/order-recognition/response-audio/{session_id}"
            except Exception as e:
                logger.error(f"生成语音回复失败: {str(e)}")
        
        return {
            "success": True,
            "recognized_items": adjustment_result["items"],
            "response": adjustment_result["response"],
            "chat_history": session["chat_history"],
            "audio_url": audio_url
        }
    
    except Exception as e:
        logger.error(f"订单调整失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"订单调整失败: {str(e)}"}
        )

@router.post("/update-item-quantity")
async def update_item_quantity(
    request: Request,
    session_id: str = Form(...),
    product_id: int = Form(...),
    quantity: int = Form(...),
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """手动更新订单项数量"""
    
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
        # 获取产品
        product_service = ProductService(db)
        product = product_service.get_product(product_id)
        if not product:
            return JSONResponse(status_code=404, content={"success": False, "message": "产品不存在"})
        
        # 更新数量
        items = session["recognized_items"]
        product_found = False
        old_quantity = 0
        
        for item in items:
            if item["product_id"] == product_id:
                old_quantity = item["quantity"]
                item["quantity"] = quantity
                product_found = True
                break
        
        # 如果产品不在列表中且数量大于0，则添加
        if not product_found and quantity > 0:
            items.append({
                "product_id": product_id,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": float(product.price),
                "unit_type": product.unit_type,
                "confidence": 1.0  # 手动添加的置信度为1
            })
            
            # 添加系统消息到历史记录
            session["chat_history"].append({
                "role": "system", 
                "content": f"已添加 {product.name} {quantity} {product.unit_type} 到订单"
            })
        elif product_found:
            if quantity > 0:
                # 更新数量
                session["chat_history"].append({
                    "role": "system", 
                    "content": f"已将 {product.name} 数量从 {old_quantity} 更新为 {quantity} {product.unit_type}"
                })
            else:
                # 移除商品
                session["chat_history"].append({
                    "role": "system", 
                    "content": f"已从订单中移除 {product.name}"
                })
        
        # 如果数量为0，则移除该项
        items = [item for item in items if item["quantity"] > 0]
        
        # 更新会话状态
        session["recognized_items"] = items
        session["last_updated"] = datetime.now()
        active_sessions[session_id] = session
        
        # 生成语音回复
        audio_url = None
        message = ""
        if product_found:
            if quantity > 0:
                message = f"已将 {product.name} 数量从 {old_quantity} 更新为 {quantity} {product.unit_type}"
            else:
                message = f"已从订单中移除 {product.name}"
        else:
            message = f"已添加 {product.name} {quantity} {product.unit_type} 到订单"
        
        if os.environ.get("ENABLE_VOICE", "false").lower() == "true":
            try:
                from ...core.voice_service import BaiduVoiceService
                audio_data = await BaiduVoiceService.text_to_speech(message)
                voice_responses[session_id] = audio_data
                audio_url = f"/api/order-recognition/response-audio/{session_id}"
            except Exception as e:
                logger.error(f"生成语音回复失败: {str(e)}")
        
        return {
            "success": True,
            "recognized_items": items,
            "message": message,
            "chat_history": session["chat_history"],
            "audio_url": audio_url
        }
    
    except Exception as e:
        logger.error(f"更新商品数量失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新商品数量失败: {str(e)}"}
        )

@router.post("/confirm-order")
async def confirm_order(
    request: Request,
    session_id: str = Form(...),
    note: Optional[str] = Form(None),
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
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
    if not session["recognized_items"] or len(session["recognized_items"]) == 0:
        return JSONResponse(status_code=400, content={"success": False, "message": "订单中没有商品，无法提交"})
    
    try:
        # 创建订单
        order_service = OrderService(db)
        new_order = order_service.create_order(int(restaurant_id), note)
        
        # 添加订单项
        total_amount = 0
        for item in session["recognized_items"]:
            product_id = item["product_id"]
            quantity = item["quantity"]
            unit_price = item["unit_price"]
            unit_type = item["unit_type"]
            
            # 检查库存
            product_service = ProductService(db)
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
        order_service.update_order_total(new_order.id)
        
        # 生成成功消息
        success_message = f"订单已成功提交，订单号: {new_order.id}"
        
        # 生成语音回复
        audio_url = None
        if os.environ.get("ENABLE_VOICE", "false").lower() == "true":
            try:
                from ...core.voice_service import BaiduVoiceService
                audio_data = await BaiduVoiceService.text_to_speech(success_message)
                voice_responses[f"order_confirmed_{new_order.id}"] = audio_data
                audio_url = f"/api/order-recognition/response-audio/order_confirmed_{new_order.id}"
            except Exception as e:
                logger.error(f"生成语音回复失败: {str(e)}")
        
        # 清理会话
        del active_sessions[session_id]
        
        return {
            "success": True,
            "order_id": new_order.id,
            "message": success_message,
            "redirect_url": get_url(f"/client/order/{new_order.id}"),
            "audio_url": audio_url
        }
    
    except Exception as e:
        logger.error(f"提交订单失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"提交订单失败: {str(e)}"}
        )

@router.get("/session/{session_id}")
async def get_session_status(
    request: Request,
    session_id: str,
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """获取会话状态"""
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    # 检查会话是否存在
    if session_id not in active_sessions:
        return JSONResponse(status_code=404, content={"success": False, "message": "会话不存在或已过期"})
    
    # 检查会话是否属于当前餐馆
    session = active_sessions[session_id]
    if session["restaurant_id"] != restaurant_id:
        return JSONResponse(status_code=403, content={"success": False, "message": "无权访问此会话"})
    
    # 返回会话状态，但排除敏感信息
    return {
        "success": True,
        "photo_url": session["photo_url"],
        "recognized_items": session["recognized_items"],
        "chat_history": session["chat_history"],
        "created_at": session["created_at"].isoformat(),
        "last_updated": session["last_updated"].isoformat()
    }

@router.get("/products/search")
async def search_products(
    request: Request,
    query: str,
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """搜索产品，用于手动添加到订单"""
    
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
                "unit_type": p.unit_type,
                "image_url": get_url(p.image_url) if p.image_url else None
            }
            for p in products
        ]
        
        return {
            "success": True,
            "products": products_list
        }
    
    except Exception as e:
        logger.error(f"搜索产品失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"搜索产品失败: {str(e)}"}
        )

# 语音相关API端点

@router.post("/speech-to-text")
async def convert_speech_to_text(
    request: Request,
    audio: UploadFile = File(...),
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none)
):
    """将语音转换为文本"""
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    try:
        # 读取音频数据
        audio_data = await audio.read()
        
        # 调用语音识别服务
        from ...core.voice_service import BaiduVoiceService
        text = await BaiduVoiceService.speech_to_text(audio_data)
        
        return {
            "success": True,
            "text": text
        }
    
    except Exception as e:
        logger.error(f"语音识别失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"语音识别失败: {str(e)}"}
        )

@router.post("/text-to-speech")
async def convert_text_to_speech(
    request: Request,
    text: str = Form(...),
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none)
):
    """将文本转换为语音"""
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    try:
        # 调用语音合成服务
        from ...core.voice_service import BaiduVoiceService
        audio_data = await BaiduVoiceService.text_to_speech(text)
        
        # 返回音频数据
        return Response(
            content=audio_data,
            media_type="audio/wav"
        )
    
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"语音合成失败: {str(e)}"}
        )

@router.post("/voice-adjust-order")
async def adjust_order_via_voice(
    request: Request,
    session_id: str = Form(...),
    audio: UploadFile = File(...),
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """通过语音调整订单内容"""
    
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
        # 读取音频数据
        audio_data = await audio.read()
        
        # 调用语音识别服务
        from ...core.voice_service import BaiduVoiceService
        message = await BaiduVoiceService.speech_to_text(audio_data)
        
        if not message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "语音识别失败，请重试"}
            )
        
        # 添加用户消息到历史记录
        session["chat_history"].append({"role": "user", "content": message})
        
        # 处理用户消息并调整订单
        adjustment_result = await process_adjustment(message, session, db)
        
        # 添加系统回复到历史记录
        session["chat_history"].append({"role": "system", "content": adjustment_result["response"]})
        
        # 更新会话状态
        session["recognized_items"] = adjustment_result["items"]
        session["last_updated"] = datetime.now()
        active_sessions[session_id] = session
        
        # 调用语音合成服务
        audio_data = await BaiduVoiceService.text_to_speech(adjustment_result["response"])
        voice_responses[session_id] = audio_data
        
        # 返回处理结果和语音回复
        return {
            "success": True,
            "recognized_items": adjustment_result["items"],
            "response": adjustment_result["response"],
            "chat_history": session["chat_history"],
            "audio_url": f"/api/order-recognition/response-audio/{session_id}",  # 音频URL
            "transcribed_text": message  # 返回识别出的文本
        }
    
    except Exception as e:
        logger.error(f"语音调整订单失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"语音调整订单失败: {str(e)}"}
        )

@router.get("/response-audio/{response_id}")
async def get_response_audio(
    request: Request,
    response_id: str,
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none)
):
    """获取语音回复"""
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    if response_id not in voice_responses:
        return JSONResponse(status_code=404, content={"success": False, "message": "语音回复不存在"})
    
    # 获取语音数据
    audio_data = voice_responses[response_id]
    
    # 返回音频数据
    return Response(
        content=audio_data,
        media_type="audio/wav"
    )

# 用于测试的端点

@router.post("/test-image-recognition")
async def test_image_recognition(
    request: Request,
    product_names: str = Form(...),  # 逗号分隔的产品名称
    restaurant_id: Optional[str] = Depends(get_current_restaurant_or_none),
    db: Session = Depends(get_db)
):
    """测试端点：模拟图像识别"""
    
    if not restaurant_id:
        return JSONResponse(status_code=401, content={"success": False, "message": "请先登录"})
    
    try:
        # 创建会话ID
        session_id = str(uuid.uuid4())
        
        # 解析产品名称
        product_name_list = [name.strip() for name in product_names.split(",") if name.strip()]
        
        # 获取所有产品
        all_products = db.query(models.Product).filter(models.Product.is_active == True).all()
        
        # 识别产品
        recognized_items = []
        original_text = f"订单内容：\n"
        
        for name in product_name_list:
            # 模拟模糊匹配
            matched_product = None
            max_similarity = 0
            
            for p in all_products:
                similarity = string_similarity(name.lower(), p.name.lower())
                if similarity > max_similarity and similarity > 0.5:
                    max_similarity = similarity
                    matched_product = p
            
            # 如果找到匹配产品
            if matched_product:
                # 随机数量1-5
                quantity = random.randint(1, 5)
                
                recognized_items.append({
                    "product_id": matched_product.id,
                    "product_name": matched_product.name,
                    "quantity": quantity,
                    "unit_price": float(matched_product.price),
                    "unit_type": matched_product.unit_type,
                    "confidence": max_similarity
                })
                
                original_text += f"{name} {quantity}{matched_product.unit_type}\n"
        
        # 存储会话状态
        active_sessions[session_id] = {
            "restaurant_id": restaurant_id,
            "photo_path": None,
            "photo_url": None,  # 测试模式，没有实际照片
            "recognized_items": recognized_items,
            "original_text": original_text,
            "chat_history": [
                {"role": "system", "content": "已识别订单内容，您可以通过对话调整订单项目。"}
            ],
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "recognized_items": recognized_items,
            "original_text": original_text,
            "message": "模拟照片识别成功"
        }
    
    except Exception as e:
        logger.error(f"测试识别失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"测试识别失败: {str(e)}"}
        )

# 辅助函数

async def save_photo(photo):
    """保存订单照片"""
    # 创建保存目录
    upload_dir = "/home/mlsp/app/static/uploads/order_photos"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_ext = os.path.splitext(photo.filename)[1]
    filename = f"order_recognition_{timestamp}{file_ext}"
    file_path = os.path.join(upload_dir, filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
    
    # 设置权限
    os.chmod(file_path, 0o777)
    
    return file_path

async def analyze_photo_with_ai(file_path, db):
    """使用AI分析照片中的订单内容（模拟实现）"""
    # 获取所有产品信息，用于匹配
    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    
    # 模拟识别结果
    # 随机选择1-4个产品作为识别结果
    sample_size = min(random.randint(1, 4), len(products))
    selected_products = random.sample(list(products), sample_size)
    
    # 构建识别结果
    recognized_items = []
    original_text = "订单内容：\n"
    
    for product in selected_products:
        # 随机数量1-5
        quantity = random.randint(1, 5)
        
        recognized_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": quantity,
            "unit_price": float(product.price),
            "unit_type": product.unit_type,
            "confidence": random.uniform(0.7, 0.99)  # 随机置信度
        })
        
        original_text += f"{product.name} {quantity}{product.unit_type}\n"
    
    return {
        "items": recognized_items,
        "original_text": original_text
    }

async def process_adjustment(message, session, db):
    """处理用户的调整消息并更新订单"""
    # 获取当前订单项
    current_items = session["recognized_items"]
    
    # 简单规则处理
    adjusted_items = current_items.copy()
    response = ""
    
    # 获取所有产品
    all_products = db.query(models.Product).filter(models.Product.is_active == True).all()
    
    # 替换操作 (如"不是X，是Y")
    if ("不是" in message or "改为" in message) and "是" in message:
        # 尝试提取旧产品和新产品名称
        old_product_name = None
        new_product_name = None
        
        # 简单解析，实际应使用NLP
        if "不是" in message:
            parts = message.split("不是")[1].split("是")
            if len(parts) >= 2:
                old_product_name = parts[0].strip()
                new_product_name = parts[1].strip().split("，")[0].split(",")[0]
        elif "改为" in message:
            parts = message.split("改为")
            if len(parts) >= 2:
                # 尝试从第一部分提取产品名
                first_part = parts[0]
                for item in current_items:
                    if item["product_name"] in first_part:
                        old_product_name = item["product_name"]
                        break
                new_product_name = parts[1].strip().split("，")[0].split(",")[0]
        
        if old_product_name and new_product_name:
            # 查找旧产品
            old_item_index = None
            old_item = None
            for i, item in enumerate(adjusted_items):
                if old_product_name in item["product_name"]:
                    old_item_index = i
                    old_item = item
                    break
            
            # 查找新产品
            new_product = None
            for p in all_products:
                if new_product_name in p.name:
                    new_product = p
                    break
            
            if old_item_index is not None and new_product:
                # 替换产品
                quantity = old_item["quantity"]
                adjusted_items[old_item_index] = {
                    "product_id": new_product.id,
                    "product_name": new_product.name,
                    "quantity": quantity,
                    "unit_price": float(new_product.price),
                    "unit_type": new_product.unit_type,
                    "confidence": 1.0
                }
                
                response = f"已将{old_product_name}替换为{new_product.name}，数量为{quantity}{new_product.unit_type}。"
            else:
                if old_item_index is None:
                    response = f"订单中没有找到{old_product_name}。"
                else:
                    response = f"没有找到{new_product_name}，请检查名称是否正确。"
    
    # 添加操作
    elif "添加" in message or "增加" in message:
        # 尝试提取产品名称和数量
        product_name = None
        quantity = 1
        
        for p in all_products:
            if p.name in message:
                product_name = p.name
                # 尝试提取数量
                parts = message.split(product_name)
                if len(parts) >= 2:
                    # 在后面部分查找数字
                    numbers = re.findall(r'\d+', parts[1])
                    if numbers:
                        quantity = int(numbers[0])
                break
        
        if product_name:
            # 查找产品
            product = None
            for p in all_products:
                if p.name == product_name:
                    product = p
                    break
            
            if product:
                # 检查是否已存在
                existing = False
                for item in adjusted_items:
                    if item["product_id"] == product.id:
                        item["quantity"] += quantity
                        existing = True
                        break
                
                if not existing:
                    # 添加新项
                    adjusted_items.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": quantity,
                        "unit_price": float(product.price),
                        "unit_type": product.unit_type,
                        "confidence": 1.0
                    })
                
                response = f"已添加{product.name} {quantity}{product.unit_type}到订单。"
            else:
                response = f"没有找到{product_name}，请检查名称是否正确。"
        else:
            response = "请指定要添加的产品名称。"
    
    # 删除操作
    elif "删除" in message or "移除" in message:
        # 尝试提取产品名称
        product_name = None
        
        for p in all_products:
            if p.name in message:
                product_name = p.name
                break
        
        if product_name:
            # 查找并删除
            for i, item in enumerate(adjusted_items):
                if product_name in item["product_name"]:
                    del adjusted_items[i]
                    response = f"已从订单中删除{product_name}。"
                    break
            else:
                response = f"订单中没有找到{product_name}。"
        else:
            response = "请指定要删除的产品名称。"
    
    # 修改数量
    elif "数量" in message or "改为" in message or "更改" in message:
        # 尝试提取产品名称和数量
        product_name = None
        quantity = None
        
        # 查找产品名
        for p in all_products:
            if p.name in message:
                product_name = p.name
                break
        
        # 查找数量
        if product_name:
            numbers = re.findall(r'\d+', message)
            if numbers:
                quantity = int(numbers[0])
        
        if product_name and quantity is not None:
            # 查找并更新
            for item in adjusted_items:
                if product_name in item["product_name"]:
                    item["quantity"] = quantity
                    response = f"已将{product_name}的数量更新为{quantity}{item['unit_type']}。"
                    break
            else:
                response = f"订单中没有找到{product_name}。"
        else:
            if not product_name:
                response = "请指定要修改的产品名称。"
            else:
                response = "请指定新的数量。"
    
    # 其他情况
    else:
        response = "我理解您想调整订单，但不确定具体操作。您可以尝试：添加产品、删除产品、或修改数量。"
    
    return {
        "items": adjusted_items,
        "response": response
    }

def string_similarity(s1, s2):
    """计算两个字符串的相似度，返回0到1之间的值"""
    # 如果一个是另一个的子字符串，返回较高相似度
    if s1 in s2:
        return len(s1) / len(s2)
    elif s2 in s1:
        return len(s2) / len(s1)
    
    # 计算公共字符
    s1_chars = set(s1)
    s2_chars = set(s2)
    common_chars = s1_chars.intersection(s2_chars)
    
    if not common_chars:
        return 0
    
    # 使用Jaccard相似度
    return len(common_chars) / len(s1_chars.union(s2_chars))
