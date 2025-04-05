# This file is maintained for backward compatibility
# The actual QR code generation is disabled

def generate_shelf_qrcode(shelf_id, shelf_name, save_dir="/home/mlsp/app/static/qrcodes/shelves"):
    """Placeholder for shelf QR code generation - no longer generates actual QR codes."""
    print(f"QR code generation for shelf {shelf_id} is disabled.")
    return f"/static/qrcodes/shelves/shelf_{shelf_id}.png"

def generate_slot_qrcode(slot_id, slot_name, save_dir="/home/mlsp/app/static/qrcodes/slots"):
    """Placeholder for slot QR code generation - no longer generates actual QR codes."""
    print(f"QR code generation for slot {slot_id} is disabled.")
    return f"/static/qrcodes/slots/slot_{slot_id}.png"

def generate_all_shelf_qrcodes(db):
    """Placeholder function that returns empty list"""
    return []
