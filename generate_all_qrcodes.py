import sys
sys.path.append('/home/mlsp')

from app.db.database import SessionLocal
from app.db import models
from app.utils.shelf_qrcode import generate_shelf_qrcode, generate_slot_qrcode

def generate_all_qrcodes():
    db = SessionLocal()
    try:
        # 获取所有货架
        shelves = db.query(models.Shelf).all()
        print(f"找到 {len(shelves)} 个货架")
        
        for shelf in shelves:
            print(f"为货架 {shelf.id}: {shelf.name} 生成二维码")
            qr_url = generate_shelf_qrcode(shelf.id, shelf.name)
            print(f"货架二维码 URL: {qr_url}")
            
            # 获取该货架下的所有货位
            slots = db.query(models.ShelfSlot).filter(models.ShelfSlot.shelf_id == shelf.id).all()
            print(f"  货架 {shelf.name} 有 {len(slots)} 个货位")
            
            for slot in slots:
                print(f"  为货位 {slot.id}: {slot.position} 生成二维码")
                slot_name = f"{shelf.name}-{slot.position}"
                slot_qr_url = generate_slot_qrcode(slot.id, slot_name)
                print(f"  货位二维码 URL: {slot_qr_url}")
        
        print("\n所有二维码已生成完毕")
    finally:
        db.close()

if __name__ == "__main__":
    generate_all_qrcodes()
