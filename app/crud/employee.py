from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
from ..db import models

def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def get_employee_by_username(db: Session, username: str):
    return db.query(models.Employee).filter(models.Employee.username == username).first()

def get_employees(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    query = db.query(models.Employee)
    if active_only:
        query = query.filter(models.Employee.is_active == True)
    return query.offset(skip).limit(limit).all()

def create_employee(
    db: Session, name: str, username: str, password: str, 
    position: Optional[str] = None, phone: Optional[str] = None, is_active: bool = True
):
    db_employee = models.Employee(
        name=name,
        username=username,
        password=password,  # 实际应用中应哈希密码
        position=position,
        phone=phone,
        is_active=is_active,
        created_at=datetime.datetime.now()
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def update_employee(
    db: Session, employee_id: int, 
    name: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    position: Optional[str] = None,
    phone: Optional[str] = None,
    is_active: Optional[bool] = None
):
    employee = get_employee(db, employee_id)
    if not employee:
        return None
    
    if name is not None:
        employee.name = name
    if username is not None:
        employee.username = username
    if password is not None and password.strip():
        employee.password = password
    if position is not None:
        employee.position = position
    if phone is not None:
        employee.phone = phone
    if is_active is not None:
        employee.is_active = is_active
    
    db.commit()
    db.refresh(employee)
    return employee

def delete_employee(db: Session, employee_id: int):
    employee = get_employee(db, employee_id)
    if not employee:
        return False
    
    db.delete(employee)
    db.commit()
    return True

def authenticate_employee(db: Session, username: str, password: str):
    employee = get_employee_by_username(db, username)
    if not employee or not employee.is_active or employee.password != password:
        return None
    return employee
