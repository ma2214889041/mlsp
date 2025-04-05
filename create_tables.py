#!/usr/bin/env python3

# 导入必要的模块
import sys
sys.path.append('/home/mlsp')

# 导入数据库模型和引擎
from app.db import models, database

# 创建所有表
print("开始创建数据库表...")
models.Base.metadata.create_all(bind=database.engine)
print("数据库表创建完成!")

# 检查表是否存在
from sqlalchemy import inspect
inspector = inspect(database.engine)

tables = inspector.get_table_names()
print(f"数据库中的表: {tables}")

# 期望的表名
expected_tables = [
    "restaurants", "products", "orders", "order_items",
    "shelves", "shelf_slots", "inventory", "employees",
    "picking_records", "order_photos"
]

# 检查每个表是否存在
for table in expected_tables:
    if table in tables:
        print(f"✓ 表 '{table}' 已存在")
    else:
        print(f"✗ 表 '{table}' 不存在!")
