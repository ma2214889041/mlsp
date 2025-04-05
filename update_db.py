from app.db import models, database
from sqlalchemy import Column, Integer
import sqlalchemy as sa

# 创建连接引擎
engine = database.engine
conn = engine.connect()

try:
    # 添加stock_threshold列到products表
    conn.execute(sa.text('ALTER TABLE products ADD COLUMN stock_threshold INTEGER DEFAULT 10'))
    
    # 设置默认值
    conn.execute(sa.text('UPDATE products SET stock_threshold = 10 WHERE stock_threshold IS NULL'))
    
    # 提交更改
    conn.commit()
    print('数据库更新成功！')
except Exception as e:
    print(f'更新数据库时出错: {str(e)}')
finally:
    conn.close()
