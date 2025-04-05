#!/usr/bin/env python3

import os
import sys
from pathlib import Path

sys.path.append('/home/mlsp')

from app.db.database import SessionLocal
from app.db import models
from app.utils.shelf_qrcode import generate_shelf_qrcode, generate_slot_qrcode

def generate_all_qrcodes():
    # 确保目录存在
    shelves_dir = "/home/mlsp/app/static/qrcodes/shelves"
    slots_dir = "/home/mlsp/app/static/qrcodes/slots"
    Path(shelves_dir).mkdir(parents=True, exist_ok=True)
    Path(slots_dir).mkdir(parents=True, exist_ok=True)
    
    # 设置权限
    os.system(f"chmod -R 777 {shelves_dir}")
    os.system(f"chmod -R 777 {slots_dir}")
    
    db = SessionLocal()
    try:
        # 获取所有货架
        shelves = db.query(models.Shelf).all()
        print(f"找到 {len(shelves)} 个货架")
        
        for shelf in shelves:
            print(f"正在处理货架 {shelf.id}: {shelf.name}")
            qr_path = os.path.join(shelves_dir, f"shelf_{shelf.id}.png")
            
            # 如果二维码不存在，则生成
            if not os.path.exists(qr_path):
                qr_url = generate_shelf_qrcode(shelf.id, shelf.name)
                print(f"  已生成货架二维码: {qr_url}")
            else:
                print(f"  货架二维码已存在: {qr_path}")
            
            # 获取货架的所有货位
            slots = db.query(models.ShelfSlot).filter(models.ShelfSlot.shelf_id == shelf.id).all()
            print(f"  货架 {shelf.name} 有 {len(slots)} 个货位")
            
            for slot in slots:
                slot_qr_path = os.path.join(slots_dir, f"slot_{slot.id}.png")
                
                # 如果二维码不存在，则生成
                if not os.path.exists(slot_qr_path):
                    slot_qr_url = generate_slot_qrcode(slot.id, f"{shelf.name}-{slot.position}")
                    print(f"    已生成货位二维码: {slot_qr_url}")
                else:
                    print(f"    货位二维码已存在: {slot_qr_path}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_all_qrcodes()
    print("所有二维码生成完毕")
