from flask import Blueprint, render_template, request
from app.models.equipment import Equipment

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    首頁：顯示設備列表
    - 可接收 `?category=` 來過濾特定種類的設備
    - 向 Model 查詢設備陣列後，渲染 index.html
    """
    # 取得 URL 查詢參數
    category = request.args.get('category')
    
    # 呼叫 Model 取得設備清單，Equipment 內部已處理 30 分鐘失效邏輯
    equipments = Equipment.get_all(category=category)
    
    # 渲染首頁模板，並將變數傳遞給前端
    return render_template('index.html', equipments=equipments, current_category=category)
