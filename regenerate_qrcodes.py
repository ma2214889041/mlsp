import sys
import os
from pathlib import Path
import qrcode

# 从应用导入数据库模型
sys.path.append('/home/mlsp')
from app.db.database import SessionLocal
from app.db import models

def generate_shelf_qrcode(shelf_id, shelf_name, save_dir="/home/mlsp/app/static/qrcodes/shelves"):
    """生成货架二维码并保存"""
    # 确保目录存在
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建二维码数据（格式：shelf:ID:名称）
    qr_data = f"shelf:{shelf_id}:{shelf_name}"
    
    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # 保存文件
    file_path = f"{save_dir}/shelf_{shelf_id}.png"
    img.save(file_path)
    print(f"已生成货架二维码: {file_path}")
    
    # 返回URL路径
    return f"/static/qrcodes/shelves/shelf_{shelf_id}.png"

def generate_slot_qrcode(slot_id, slot_name, save_dir="/home/mlsp/app/static/qrcodes/slots"):
    """生成货位二维码并保存"""
    # 确保目录存在
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建二维码数据（格式：slot:ID:名称）
    qr_data = f"slot:{slot_id}:{slot_name}"
    
    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # 保存文件
    file_path = f"{save_dir}/slot_{slot_id}.png"
    img.save(file_path)
    print(f"已生成货位二维码: {file_path}")
    
    # 返回URL路径
    return f"/static/qrcodes/slots/slot_{slot_id}.png"

def regenerate_all_qrcodes():
    """重新生成所有货架和货位的二维码"""
    db = SessionLocal()
    try:
        # 获取所有货架
        shelves = db.query(models.Shelf).all()
        print(f"找到 {len(shelves)} 个货架")
        
        # 为每个货架生成二维码
        for shelf in shelves:
            generate_shelf_qrcode(shelf.id, shelf.name)
            
            # 为货架上的每个货位生成二维码
            slots = db.query(models.ShelfSlot).filter(models.ShelfSlot.shelf_id == shelf.id).all()
            print(f"货架 {shelf.name} 有 {len(slots)} 个货位")
            
            for slot in slots:
                generate_slot_qrcode(slot.id, f"{shelf.name}-{slot.position}")
                
        print("所有二维码已重新生成")
    finally:
        db.close()

if __name__ == "__main__":
    regenerate_all_qrcodes()
