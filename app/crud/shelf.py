from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
from ..db import models

def get_shelf(db: Session, shelf_id: int):
    return db.query(models.Shelf).filter(models.Shelf.id == shelf_id).first()

def get_shelves(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Shelf).offset(skip).limit(limit).all()

def create_shelf(db: Session, name: str, location: str):
    db_shelf = models.Shelf(
        name=name,
        location=location,
        created_at=datetime.datetime.now()
    )
    db.add(db_shelf)
    db.commit()
    db.refresh(db_shelf)
    return db_shelf

def update_shelf(db: Session, shelf_id: int, name: str, location: str):
    shelf = get_shelf(db, shelf_id)
    if not shelf:
        return None
    
    shelf.name = name
    shelf.location = location
    
    db.commit()
    db.refresh(shelf)
    return shelf

def delete_shelf(db: Session, shelf_id: int):
    shelf = get_shelf(db, shelf_id)
    if not shelf:
        return False
    
    db.delete(shelf)
    db.commit()
    return True

def get_shelf_slot(db: Session, slot_id: int):
    return db.query(models.ShelfSlot).filter(models.ShelfSlot.id == slot_id).first()

def get_shelf_slots(db: Session, shelf_id: int):
    return db.query(models.ShelfSlot).filter(models.ShelfSlot.shelf_id == shelf_id).all()

def create_shelf_slot(db: Session, shelf_id: int, position: str):
    db_slot = models.ShelfSlot(
        shelf_id=shelf_id,
        position=position,
        created_at=datetime.datetime.now()
    )
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def delete_shelf_slot(db: Session, slot_id: int):
    slot = get_shelf_slot(db, slot_id)
    if not slot:
        return False
    
    db.delete(slot)
    db.commit()
    return True

def get_shelf_stats(db: Session):
    total_shelves = db.query(models.Shelf).count()
    total_slots = db.query(models.ShelfSlot).count()
    occupied_slots = db.query(models.ShelfSlot).join(models.Inventory, models.ShelfSlot.id == models.Inventory.slot_id, isouter=True).filter(models.Inventory.id != None).count()
    empty_slots = total_slots - occupied_slots
    
    return {
        "total_shelves": total_shelves,
        "total_slots": total_slots,
        "occupied_slots": occupied_slots,
        "empty_slots": empty_slots
    }
