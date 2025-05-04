from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ...core.deps import get_db
from ...core.config import get_url
from ...services.client_service import ProductService
from ...db import models

router = APIRouter()

# 创建日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("barcode_api")

# 条形码处理函数
def normalize_barcode(barcode):
    """规范化条形码，去除空格和特殊字符"""
    if not barcode:
        return ""
    
    # 记录原始条形码信息    
    logger.info(f"处理条形码: '{barcode}', 长度: {len(barcode)}")
    
    # 检查是否包含非字母数字字符
    special_chars = [c for c in barcode if not c.isalnum()]
    if special_chars:
        logger.info(f"条形码包含特殊字符: {special_chars}")
    
    # 移除所有非字母数字字符
    normalized = ''.join(c for c in barcode if c.isalnum())
    
    # 如果处理后的条形码与原始条形码不同，记录日志
    if normalized != barcode:
        logger.info(f"规范化后的条形码: '{normalized}', 长度: {len(normalized)}")
    
    return normalized

# 检查条形码是否已存在
@router.get("/admin/api/check-barcode")
async def check_barcode(
    barcode: str,
    exclude_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """检查条形码是否已被使用"""
    logger.info(f"检查条形码: '{barcode}', 排除ID: {exclude_id}")
    
    # 规范化条形码
    normalized_barcode = normalize_barcode(barcode)
    
    # 查询产品
    query = db.query(models.Product)
    
    # 尝试使用原始条形码和规范化条形码进行查询
    product = query.filter(models.Product.barcode == barcode).first()
    if not product:
        product = query.filter(models.Product.barcode == normalized_barcode).first()
    
    # 如果提供了排除ID，则排除该产品
    if exclude_id and product and product.id == exclude_id:
        logger.info(f"找到产品(ID:{product.id})但被排除")
        return {"exists": False}
    
    if product:
        logger.info(f"条形码已存在, 产品ID: {product.id}, 名称: {product.name}")
        return {
            "exists": True,
            "product_id": product.id,
            "product_name": product.name
        }
    else:
        logger.info(f"条形码不存在")
        return {"exists": False}

# 通过条形码获取产品信息
@router.get("/api/product-by-barcode")
async def get_product_by_barcode(
    barcode: str,
    db: Session = Depends(get_db)
):
    """根据条形码获取产品信息"""
    logger.info(f"查询条形码: '{barcode}'")
    
    # 规范化条形码
    normalized_barcode = normalize_barcode(barcode)
    
    # 尝试使用多种方式查找产品
    product = None
    search_methods = [
        ("原始条形码", barcode),
        ("规范化条形码", normalized_barcode)
    ]
    
    # 尝试不同的搜索方法
    for method_name, search_barcode in search_methods:
        if search_barcode:
            product = db.query(models.Product).filter(models.Product.barcode == search_barcode).first()
            if product:
                logger.info(f"使用{method_name}找到产品: ID={product.id}, 名称={product.name}")
                break
    
    # 如果未找到产品，记录所有现有条形码以便调试
    if not product:
        all_barcodes = db.query(models.Product.id, models.Product.name, models.Product.barcode).all()
        logger.info(f"未找到产品, 当前数据库中的条形码:")
        for id, name, db_barcode in all_barcodes:
            if db_barcode:  # 只记录有条形码的产品
                logger.info(f"  ID: {id}, 名称: {name}, 条形码: '{db_barcode}'")
        
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "未找到该条形码对应的产品"}
        )
    
    # 处理图片URL，确保添加了前缀
    image_url = product.image_url
    if image_url:
        image_url = get_url(image_url)
    
    # 返回找到的产品信息
    return {
        "success": True,
        "product": {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "image_url": image_url,
            "unit_type": product.unit_type,
            "expiry_days": product.expiry_days,
            "barcode": product.barcode  # 返回原始条形码
        }
    }
