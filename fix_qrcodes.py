import sys
import os
sys.path.append('/home/mlsp')

from app.db.database import SessionLocal
from app.db import models
import qrcode
from pathlib import Path

def create_qrcode(data, file_path):
    """创建并保存二维码"""
    img = qrcode.make(data)
    img.save(file_path)
    print(f"已创建二维码: {file_path}")

def ensure_directories():
    """确保二维码目录存在"""
    paths = [
        "/home/mlsp/app/static/qrcodes",
        "/home/mlsp/app/static/qrcodes/shelves",
        "/home/mlsp/app/static/qrcodes/slots"
    ]
    for path in paths:
        os.makedirs(path, exist_ok=True)
        os.chmod(path, 0o777)  # 设置777权限确保可写

def fix_qrcodes():
    """修复所有货架和货位的二维码"""
    ensure_directories()
    
    db = SessionLocal()
    try:
        # 获取所有货架
        shelves = db.query(models.Shelf).all()
        print(f"找到 {len(shelves)} 个货架")
        
        for shelf in shelves:
            # 为货架创建二维码
            shelf_data = f"shelf:{shelf.id}:{shelf.name}"
            shelf_path = f"/home/mlsp/app/static/qrcodes/shelves/shelf_{shelf.id}.png"
            create_qrcode(shelf_data, shelf_path)
            
            # 获取货架的所有货位
            slots = db.query(models.ShelfSlot).filter(models.ShelfSlot.shelf_id == shelf.id).all()
            print(f"  货架 {shelf.name} 有 {len(slots)} 个货位")
            
            for slot in slots:
                # 为货位创建二维码
                slot_data = f"slot:{slot.id}:{shelf.name}-{slot.position}"
                slot_path = f"/home/mlsp/app/static/qrcodes/slots/slot_{slot.id}.png"
                create_qrcode(slot_data, slot_path)
    finally:
        db.close()
    
    print("\n所有二维码已修复完毕")
    
if __name__ == "__main__":
    fix_qrcodes()
