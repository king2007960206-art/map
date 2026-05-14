# 路由與頁面設計文件 (Routes)：校園設施體感地圖

## 1. 路由總覽表格

| 功能 | HTTP 方法 | URL 路徑 | 對應模板 / 回傳 | 說明 |
| ---- | --------- | -------- | --------------- | ---- |
| 首頁 / 設備列表 | GET | `/` | `templates/index.html` | 顯示所有設備列表，支援 `?category=` 參數篩選 |
| 狀態回報 API | POST | `/api/equipment/<id>/status` | JSON | 接收前端 AJAX 請求，新增狀態紀錄並回傳最新狀態 |
| 管理員儀表板 | GET | `/admin` | `templates/admin.html` | 顯示各項設備狀態的統計圖表資料 |

---

## 2. 每個路由的詳細說明

### 2.1 首頁 / 設備列表
- **URL**: `GET /`
- **輸入**: 
  - URL Query String: `category` (字串，選填，例如 `printer`)
- **處理邏輯**: 
  - 呼叫 `Equipment.get_all(category)` 取得設備資料（包含 30 分鐘自動失效處理後的最新狀態）。
- **輸出**: 渲染 `index.html`，並將設備資料陣列傳入模板。
- **錯誤處理**: 即使該分類下無設備，也是回傳 200 並於模板顯示「目前無此類設備資料」。

### 2.2 狀態回報 API (非同步處理)
- **URL**: `POST /api/equipment/<id>/status`
- **輸入**:
  - URL Parameter: `id` (整數，設備 ID)
  - JSON Body: `{"status": "available" | "queuing" | "maintenance"}`
- **處理邏輯**:
  - 驗證傳入的 `status` 字串是否在合法範圍內。
  - 檢查對應的設備 `id` 是否存在（可透過 `Equipment.get_by_id`）。
  - 若一切合法，呼叫 `StatusLog.create(id, status)` 新增紀錄。
- **輸出**: 回傳 JSON，例如 `{"success": true, "status": "queuing"}`。
- **錯誤處理**: 
  - 若 `id` 不存在，回傳 HTTP 404 與錯誤訊息。
  - 若 `status` 不合法或未帶參數，回傳 HTTP 400 與錯誤訊息。

### 2.3 管理員儀表板
- **URL**: `GET /admin`
- **輸入**: 無
- **處理邏輯**:
  - 呼叫 `StatusLog.get_stats()` 取得所有狀態的回報總結。
- **輸出**: 渲染 `admin.html`，並將統計陣列資料傳入。
- **錯誤處理**: MVP 階段無強制登入，發生異常時走預設 500 處理。

---

## 3. Jinja2 模板清單

| 模板路徑 | 繼承對象 | 用途 |
| -------- | -------- | ---- |
| `templates/base.html` | 無 | 系統基礎版型，包含 HTML 架構、引入 CSS/JS、頂部導覽列 |
| `templates/index.html`| `base.html` | 首頁：上方為分類按鈕，下方為設備狀態卡片網格 |
| `templates/admin.html`| `base.html` | 管理員頁面：以資料表方式呈現設備故障與排隊次數統計 |
