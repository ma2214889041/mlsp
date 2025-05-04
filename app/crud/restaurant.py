from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import models

def get_restaurant(db: Session, restaurant_id: int):
    return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

def get_restaurant_by_username(db: Session, username: str):
    return db.query(models.Restaurant).filter(models.Restaurant.username == username).first()

def get_restaurants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Restaurant).offset(skip).limit(limit).all()

def create_restaurant(
    db: Session, name: str, address: str, phone: str, username: str, password: str
):
    db_restaurant = models.Restaurant(
        name=name,
        address=address,
        phone=phone,
        username=username,
        password=password  # 实际应用中应哈希密码
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def update_restaurant(db: Session, restaurant_id: int, **kwargs):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        return None
    
    for key, value in kwargs.items():
        if hasattr(restaurant, key):
            setattr(restaurant, key, value)
    
    db.commit()
    db.refresh(restaurant)
    return restaurant

def authenticate_restaurant(db: Session, username: str, password: str):
    restaurant = get_restaurant_by_username(db, username)
    if not restaurant or restaurant.password != password:
        return None
    return restaurant
