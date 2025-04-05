#!/usr/bin/env python3

# 导入必要的模块
import sys
sys.path.append('/home/mlsp')

from app.db.database import SessionLocal
from app.db import models
from app.utils.shelf_qrcode import generate_shelf_qrcode, generate_slot_qrcode
import datetime

# 创建测试数据
def create_test_data():
    db = SessionLocal()
    try:
        # 创建员工
        if db.query(models.Employee).count() == 0:
            employee = models.Employee(
                name="测试员工",
                username="worker",
                password="password",
                position="仓库管理员",
                is_active=True
            )
            db.add(employee)
            db.commit()
            print("已创建测试员工")

        # 创建货架
        if db.query(models.Shelf).count() == 0:
            # 创建第一个货架
            shelf1 = models.Shelf(
                name="冷藏区货架A",
                location="仓库北侧",
                created_at=datetime.datetime.now()
            )
            db.add(shelf1)
            db.commit()
            db.refresh(shelf1)
            print(f"已创建货架: {shelf1.name}")

            # 为第一个货架生成二维码
            qr_url = generate_shelf_qrcode(shelf1.id, shelf1.name)
            print(f"已生成货架二维码: {qr_url}")

            # 为第一个货架添加货位
            positions = ["A1", "A2", "A3", "B1", "B2", "B3"]
            for pos in positions:
                slot = models.ShelfSlot(
                    shelf_id=shelf1.id,
                    position=pos,
                    created_at=datetime.datetime.now()
                )
                db.add(slot)
                db.commit()
                db.refresh(slot)
                print(f"已创建货位: {shelf1.name}-{pos}")
                
                # 为货位生成二维码
                slot_qr_url = generate_slot_qrcode(slot.id, f"{shelf1.name}-{pos}")
                print(f"已生成货位二维码: {slot_qr_url}")

            # 创建第二个货架
            shelf2 = models.Shelf(
                name="干货区货架B",
                location="仓库南侧",
                created_at=datetime.datetime.now()
            )
            db.add(shelf2)
            db.commit()
            db.refresh(shelf2)
            print(f"已创建货架: {shelf2.name}")

            # 为第二个货架生成二维码
            qr_url = generate_shelf_qrcode(shelf2.id, shelf2.name)
            print(f"已生成货架二维码: {qr_url}")

            # 为第二个货架添加货位
            positions = ["C1", "C2", "C3", "D1", "D2", "D3"]
            for pos in positions:
                slot = models.ShelfSlot(
                    shelf_id=shelf2.id,
                    position=pos,
                    created_at=datetime.datetime.now()
                )
                db.add(slot)
                db.commit()
                db.refresh(slot)
                print(f"已创建货位: {shelf2.name}-{pos}")
                
                # 为货位生成二维码
                slot_qr_url = generate_slot_qrcode(slot.id, f"{shelf2.name}-{pos}")
                print(f"已生成货位二维码: {slot_qr_url}")

        print("测试数据创建完成!")
    except Exception as e:
        print(f"创建测试数据时出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
