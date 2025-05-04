from sqlalchemy.orm import Session
from typing import List, Optional
from ..db import models
import datetime

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    query = db.query(models.Product)
    if active_only:
        query = query.filter(models.Product.is_active == True)
    return query.offset(skip).limit(limit).all()

def get_available_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product)\
        .filter(models.Product.stock > 0, models.Product.is_active == True)\
        .offset(skip).limit(limit).all()

def create_product(db: Session, name: str, description: str, price: float, 
                  stock: int, image_url: str, unit_type: str = "份"):
    # 规范化图片URL，确保不包含/mlsp前缀
    if image_url and image_url.startswith('/mlsp'):
        image_url = image_url[5:]  # 去掉/mlsp前缀
        
    db_product = models.Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        image_url=image_url,
        unit_type=unit_type,
        is_active=True
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, **kwargs):
    product = get_product(db, product_id)
    if not product:
        return None
    
    # 处理image_url
    if 'image_url' in kwargs and kwargs['image_url']:
        # 确保image_url不包含/mlsp前缀
        if kwargs['image_url'].startswith('/mlsp'):
            kwargs['image_url'] = kwargs['image_url'][5:]
    
    for key, value in kwargs.items():
        if hasattr(product, key):
            setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    if not product:
        return False
    
    db.delete(product)
    db.commit()
    return True

def get_low_stock_products(db: Session, limit: int = 5):
    return db.query(models.Product).order_by(models.Product.stock).limit(limit).all()
