from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from ...core.deps import get_db, get_current_admin, redirect_with_prefix
from ...core.config import get_prefixed_url, BASE_PATH
from ...crud import shelf
from ...db import models

router = APIRouter()
templates = Jinja2Templates(directory="/home/mlsp/app/templates")
templates.env.globals["root_path"] = BASE_PATH  # 添加全局变量
templates.env.globals["url_for"] = get_prefixed_url  # 添加URL辅助函数

@router.get("/shelf/add", response_class=HTMLResponse)
async def shelf_add_form(request: Request, admin: bool = Depends(get_current_admin)):
    # 使用模板文件 admin/shelf_add.html，如果没有可直接返回简单 HTML
    html_content = """
    <html>
      <body>
        <h2>添加货架</h2>
        <form action="/admin/shelf/add" method="post">
          货架名称: <input type="text" name="name"><br>
          位置描述: <input type="text" name="location"><br>
          <input type="submit" value="添加货架">
        </form>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/shelf/add")
async def add_shelf(request: Request, name: str = Form(...), location: str = Form(...),
                    db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    new_shelf = shelf.create_shelf(db, name, location)
    return redirect_with_prefix(f"/admin/shelf/{new_shelf.id}")

@router.get("/shelf/{shelf_id}", response_class=HTMLResponse)
async def view_shelf(request: Request, shelf_id: int, db: Session = Depends(get_db),
                     admin: bool = Depends(get_current_admin)):
    shelf_obj = db.query(models.Shelf).filter(models.Shelf.id == shelf_id).first()
    if not shelf_obj:
        raise HTTPException(status_code=404, detail="货架不存在")
    shelf_slots = shelf.get_shelf_slots(db, shelf_id)
    
    # 这里返回简单的 HTML 展示货架和货位信息，同时提示二维码文件存储位置
    html_content = f"""
    <html>
      <body>
        <h2>货架详情</h2>
        <p>货架ID: {shelf_obj.id}</p>
        <p>名称: {shelf_obj.name}</p>
        <p>位置: {shelf_obj.location}</p>
        <p>二维码: {get_prefixed_url(f"/static/qrcodes/shelves/shelf_{shelf_obj.id}.png")}</p>
        <h3>货位列表</h3>
        <ul>
    """
    for slot in shelf_slots:
        html_content += f"<li>货位ID: {slot.id}，标识: {slot.position}，二维码: {get_prefixed_url(f"/static/qrcodes/slots/shelf_{shelf_obj.id}_slot_{slot.id}.png")}</li>"
    html_content += """
        </ul>
        <a href="/admin/shelf/{0}/slot/add">添加货位</a>
      </body>
    </html>
    """.format(shelf_obj.id)
    return HTMLResponse(content=html_content)

@router.get("/shelf/{shelf_id}/slot/add", response_class=HTMLResponse)
async def shelf_slot_add_form(request: Request, shelf_id: int, admin: bool = Depends(get_current_admin)):
    html_content = f"""
    <html>
      <body>
        <h2>为货架 {shelf_id} 添加货位</h2>
        <form action="{get_prefixed_url(f"/admin/shelf/{shelf_id}/slot/add")}" method="post">
          货位标识: <input type="text" name="position"><br>
          <input type="submit" value="添加货位">
        </form>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/shelf/{shelf_id}/slot/add")
async def add_shelf_slot(request: Request, shelf_id: int, position: str = Form(...),
                         db: Session = Depends(get_db), admin: bool = Depends(get_current_admin)):
    new_slot = shelf.create_shelf_slot(db, shelf_id, position)
    return redirect_with_prefix(f"/admin/shelf/{shelf_id}")

@router.post("/shelf/{shelf_id}/delete")
async def delete_shelf(request: Request, shelf_id: int, db: Session = Depends(get_db),
                       admin: bool = Depends(get_current_admin)):
    shelf.delete_shelf(db, shelf_id)
    return redirect_with_prefix("/admin/shelves")

@router.post("/slot/{slot_id}/delete")
async def delete_shelf_slot(request: Request, slot_id: int, db: Session = Depends(get_db),
                            admin: bool = Depends(get_current_admin)):
    shelf.delete_shelf_slot(db, slot_id)
    return redirect_with_prefix("/admin/shelves")

@router.get("/shelves", response_class=HTMLResponse)
async def list_shelves(request: Request, db: Session = Depends(get_db),
                       admin: bool = Depends(get_current_admin)):
    shelves_list = shelf.get_shelves(db)
    html_content = "<html><body><h2>所有货架</h2><ul>"
    for s in shelves_list:
        html_content += f'<li><a href="{get_prefixed_url(f"/admin/shelf/{s.id}")}">{s.name}</a></li>'
    html_content += "</ul></body></html>"
    return HTMLResponse(content=html_content)
