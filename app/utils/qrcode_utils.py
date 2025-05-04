import qrcode
import io
import base64
from pathlib import Path
from ..core.config import get_url

def generate_qrcode(data, size=10):
    """生成二维码并返回base64编码的图像"""
    # 使用更简单的qrcode创建方法
    img = qrcode.make(data)
    
    # 转换为base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}"

def generate_order_qrcode(order_id, base_url="https://milan.food.co"):
    """生成订单的二维码数据"""
    # 二维码中包含订单ID和验证网址
    data = f"milan-order:{order_id}"
    return generate_qrcode(data)

def save_order_qrcode(order_id, save_dir="/home/mlsp/app/static/qrcodes"):
    """生成订单二维码并保存为文件"""
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 使用简化版的API，直接使用前缀格式
    data = f"milan-order:{order_id}"
    img = qrcode.make(data)
    
    file_path = f"{save_dir}/order_{order_id}.png"
    img.save(file_path)
    # 修改返回URL，使用get_prefixed_url函数
    return get_url(f"/static/qrcodes/order_{order_id}.png")
