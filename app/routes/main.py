from flask import Blueprint, render_template, request
from app.models import Equipment

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    首頁：顯示設備列表
    - 可接收 `?category=` 來過濾特定種類的設備
    - 向 Model 查詢設備陣列後，渲染 index.html
    """
    pass
