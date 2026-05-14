# 系統架構文件 (Architecture)：校園設施體感地圖

## 1. 技術架構說明

本專案定位為輕量化的校園資訊回報平台，並採用傳統的 MVC（Model-View-Controller）架構搭配伺服器端渲染（Server-Side Rendering），以求快速開發與穩定佈署。

### 選用技術與原因
- **後端框架：Python + Flask**
  - **原因**：Flask 是輕量級的後端框架，非常適合做功能單純、快速迭代的 MVP 專案。學習曲線平緩，對初學者友善。
- **模板引擎：Jinja2**
  - **原因**：內建於 Flask，可直接在後端把資料渲染到 HTML 中送給前端，不需要複雜的前後端分離架構與 API 介接，大幅降低開發門檻。
- **資料庫：SQLite (搭配 SQLAlchemy 或內建 sqlite3)**
  - **原因**：無需額外安裝或設定獨立的資料庫伺服器，資料儲存在單一檔案中，適合此類輕量化、資料關聯單純的微型專案。
- **前端：Vanilla HTML / CSS / JS**
  - **原因**：在 Jinja2 基礎上，使用原生語法即可滿足行動版優先的排版。需要動態更新的地方（如標註狀態）可以透過簡單的 JS 處理。

### Flask MVC 模式說明
雖然 Flask 本身沒有強制規定 MVC，但我們會依照此概念來組織程式碼：
- **Model (模型)**：負責與 SQLite 溝通，定義「設備」、「狀態紀錄」等資料結構與資料存取邏輯。
- **View (視圖)**：Jinja2 模板（`.html`），負責將 Controller 整理好的資料，以 HTML 形式呈現給瀏覽器。
- **Controller (控制器)**：Flask 的路由函式（`routes`），負責接收使用者的請求（如：查看設備列表、提交狀態更新），向 Model 獲取或更新資料，最後交由 View 渲染畫面並回傳。

---

## 2. 專案資料夾結構

本專案建議採用以下資料夾結構，以分離不同職責的程式碼，便於後續維護與擴充：

```text
app/
├── models/             ← 資料庫模型 (Models)
│   ├── __init__.py
│   ├── equipment.py    ← 設備資料結構 (如：影印機、飲水機)
│   └── status_log.py   ← 設備狀態紀錄 (記錄狀態改變的歷史)
├── routes/             ← Flask 路由 (Controllers)
│   ├── __init__.py
│   ├── main.py         ← 首頁與設備列表相關路由
│   ├── api.py          ← 狀態更新、非同步回報使用的輕量 API 路由
│   └── admin.py        ← 後台統計相關路由
├── templates/          ← Jinja2 HTML 模板 (Views)
│   ├── base.html       ← 共用版型 (包含導覽列、頁首頁尾)
│   ├── index.html      ← 設備列表首頁
│   ├── admin.html      ← 管理員統計儀表板
│   └── components/     ← 可重複使用的介面元件 (如單一設備卡片)
└── static/             ← 靜態資源檔案
    ├── css/
    │   └── style.css   ← 客製化樣式表
    ├── js/
    │   └── main.js     ← 前端互動邏輯 (如點擊按鈕即時更新狀態)
    └── img/            ← 圖片與圖示資源
instance/
└── database.db         ← SQLite 資料庫檔案 (需加入 .gitignore 避免上傳)
docs/
├── PRD.md              ← 產品需求文件
└── ARCHITECTURE.md     ← 系統架構文件 (本文件)
app.py                  ← 專案進入點 (主程式)
requirements.txt        ← Python 相依套件清單
.gitignore              ← 排除不需要進入版本控制的檔案
```

---

## 3. 元件關係圖

以下是系統運作的資料流與元件互動示意圖：

```mermaid
flowchart TD
    Client[瀏覽器 Browser]

    subgraph Flask App
        Route[Flask Route\n(Controller)]
        Model[Database Model\n(Model)]
        Template[Jinja2 Template\n(View)]
    end

    DB[(SQLite 資料庫)]

    %% 讀取流程 (查看設備列表)
    Client -- "1. HTTP GET (請求頁面)" --> Route
    Route -- "2. 查詢最新設備狀態" --> Model
    Model -- "3. SQL 查詢" --> DB
    DB -- "4. 回傳資料" --> Model
    Model -- "5. 將資料交給 Route" --> Route
    Route -- "6. 結合資料進行渲染" --> Template
    Template -- "7. 回傳 HTML 頁面" --> Route
    Route -- "8. HTTP Response (顯示網頁)" --> Client

    %% 寫入流程 (群眾標註狀態)
    Client -- "A. HTTP POST (提交標註: 排隊中)" --> Route
    Route -- "B. 建立狀態紀錄" --> Model
    Model -- "C. SQL 新增/更新" --> DB
```

---

## 4. 關鍵設計決策

1. **SSR 與非同步更新（AJAX）的混搭應用**
   - **原因**：頁面的初次載入由 Flask + Jinja2 處理（SSR），開發快速且利於 SEO。但在「點擊按鈕標註狀態」時，為提供流暢的手機端體驗，會使用 JavaScript 的 Fetch API 傳送請求，讓按鈕的狀態能即時改變而無需重新整理整個網頁。
2. **狀態時效性的被動更新（Lazy Evaluation）**
   - **原因**：PRD 要求狀態過期（如 30 分鐘後）需自動失效。比起在背景執行定時任務（Cron Job）定期掃描資料庫（設定較複雜），系統會採用「被動計算」：當使用者載入列表時，程式若發現某設備最後一筆狀態的時間已超過 30 分鐘，就自動在畫面上將其顯示為「可用 / 預設狀態」，大幅降低後端實作負擔。
3. **資料庫拆分「設備表」與「狀態紀錄表」**
   - **原因**：若只在設備表中存放「當前狀態」，將無法進行歷史分析。拆分出獨立的狀態紀錄表，不僅能透過關聯查詢最新狀態，還能完整保存所有變更軌跡，滿足 PRD 中「歷史統計儀表板」的需求（統計哪些區域長期處於設備維修或大排長龍的狀態）。
4. **輕量化的無登入標註機制**
   - **原因**：為了鼓勵學生隨手回報，MVP 階段不強制註冊與登入。系統可先運用瀏覽器 Session/Cookie 搭配後端的簡單 IP 頻率限制來防止惡意洗版，減少使用者參與回報的第一道門檻。
