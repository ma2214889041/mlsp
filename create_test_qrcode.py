import qrcode
import os
from pathlib import Path

# 确保目录存在
shelves_dir = "/home/mlsp/app/static/qrcodes/shelves"
slots_dir = "/home/mlsp/app/static/qrcodes/slots"
Path(shelves_dir).mkdir(parents=True, exist_ok=True)
Path(slots_dir).mkdir(parents=True, exist_ok=True)

# 创建测试货架二维码
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data("shelf:1:测试货架")
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save(os.path.join(shelves_dir, "shelf_1.png"))
print(f"已创建测试货架二维码: {os.path.join(shelves_dir, 'shelf_1.png')}")

# 创建测试货位二维码
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data("slot:1:测试货位")
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save(os.path.join(slots_dir, "slot_1.png"))
print(f"已创建测试货位二维码: {os.path.join(slots_dir, 'slot_1.png')}")
