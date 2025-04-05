from app.db import models, database
from app.core.config import ADMIN_USERNAME, ADMIN_PASSWORD
import datetime

# 重新创建所有表
models.Base.metadata.create_all(bind=database.engine)

# 创建一些初始数据
with database.SessionLocal() as db:
    # 创建管理员用户 (如果需要)
    # 创建示例员工
    employee = models.Employee(
        name="测试员工",
        username="employee",
        password="password",
        position="仓库管理员",
        is_active=True,
        created_at=datetime.datetime.now()
    )
    db.add(employee)
    
    # 创建示例货架
    shelf1 = models.Shelf(
        name="冷藏区A架",
        location="仓库东侧",
        created_at=datetime.datetime.now()
    )
    shelf2 = models.Shelf(
        name="干货区B架",
        location="仓库西侧",
        created_at=datetime.datetime.now()
    )
    db.add(shelf1)
    db.add(shelf2)
    db.commit()
    
    # 为货架添加货位
    positions = ["A1", "A2", "A3", "B1", "B2", "B3"]
    for pos in positions[:3]:
        slot = models.ShelfSlot(
            shelf_id=shelf1.id,
            position=pos,
            created_at=datetime.datetime.now()
        )
        db.add(slot)
    
    for pos in positions[3:]:
        slot = models.ShelfSlot(
            shelf_id=shelf2.id,
            position=pos,
            created_at=datetime.datetime.now()
        )
        db.add(slot)
    
    db.commit()
    
    # 创建示例产品
    products = [
        {
            "name": "意大利面",
            "description": "高品质杜兰小麦制成的意大利面",
            "price": 15.50,
            "stock": 100,
            "image_url": "/static/uploads/products/pasta.jpg",
            "unit_type": "袋",
            "expiry_days": 365,
            "stock_threshold": 20,
            "barcode": "8001250123794"
        },
        {
            "name": "橄榄油",
            "description": "特级初榨橄榄油，来自托斯卡纳",
            "price": 68.00,
            "stock": 50,
            "image_url": "/static/uploads/products/olive_oil.jpg",
            "unit_type": "瓶",
            "expiry_days": 180,
            "stock_threshold": 10,
            "barcode": "8002930000165"
        },
        {
            "name": "番茄酱",
            "description": "纯天然番茄制作，无添加",
            "price": 12.80,
            "stock": 80,
            "image_url": "/static/uploads/products/tomato_sauce.jpg",
            "unit_type": "瓶",
            "expiry_days": 90,
            "stock_threshold": 15,
            "barcode": "8076809523738"
        }
    ]
    
    for product_data in products:
        product = models.Product(**product_data)
        db.add(product)
    
    db.commit()
    
    # 创建示例餐馆
    restaurant = models.Restaurant(
        name="测试餐厅",
        address="测试地址123号",
        phone="12345678910",
        username="restaurant",
        password="password"
    )
    db.add(restaurant)
    db.commit()
    
    print("数据库初始化完成！")
