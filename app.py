from app import create_app
from app.models.db import init_db
import os

# 初始化應用程式
app = create_app()

# 初始化資料庫
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
