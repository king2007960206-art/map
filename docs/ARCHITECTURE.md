# 系統架構設計 (ARCHITECTURE)

## 專案名稱
校園設施體感地圖

---

## 1. 技術架構說明

### 選用技術與原因
- **後端框架：Python + Flask**
  - **原因**：Flask 是輕量級的網頁框架，非常適合打造 MVP（最小可行性產品）與微型服務。本專案核心需求為快速寫入與讀取地點狀態，使用 Flask 能以最少程式碼快速建立路由與邏輯。
- **模板引擎：Jinja2**
  - **原因**：與 Flask 高度整合，支援伺服器端渲染 (SSR)。本專案不需複雜的前端框架（如 React/Vue），由 Jinja2 直接產生 HTML 頁面，不僅降低開發門檻，也確保頁面載入速度。
- **資料庫：SQLite**
  - **原因**：輕量、無需額外架設資料庫伺服器。資料直接儲存於單一檔案中，適合初期資料量不大、且主要處理讀寫頻率中等情境的校園應用。

### Flask MVC 模式說明
儘管 Flask 本身不強迫使用特定架構，本專案將採用類似 MVC（Model-View-Controller）的模式進行開發，以確保程式碼的可維護性：
- **Model（模型）**：定義 SQLite 資料表結構，處理與資料庫的溝通（如儲存新的體感回報、查詢歷史紀錄）。
- **View（視圖）**：Jinja2 HTML 模板與前端靜態資源（CSS/JS），負責呈現即時狀態清單與回報介面給使用者。
- **Controller（控制器）**：Flask 的路由（Routes），負責接收使用者請求（例如點擊回報按鈕）、呼叫 Model 處理資料，最後將結果與資料傳遞給 View 進行渲染。
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

本專案依循模組化設計，將路由、模型與模板分離：

```text
campus_sensory_map/
│
├── app/                      # 主要應用程式資料夾
│   ├── __init__.py           # Flask App 初始化設定
│   ├── models/               # 資料庫模型 (Model)
│   │   ├── __init__.py
│   │   ├── location.py       # 地點相關資料模型
│   │   └── report.py         # 體感回報紀錄模型
│   ├── routes/               # Flask 路由 (Controller)
│   │   ├── __init__.py
│   │   ├── main_routes.py    # 主頁、地圖瀏覽相關路由
│   │   └── api_routes.py     # 處理回報送出等 API 邏輯
│   ├── templates/            # Jinja2 HTML 模板 (View)
│   │   ├── base.html         # 共用版型（Header, Footer）
│   │   ├── index.html        # 首頁（地圖/狀態清單）
│   │   └── dashboard.html    # 管理員數據看板
│   └── static/               # CSS / JS 靜態資源
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── main.js       # 處理自動定位、三秒回報邏輯
│       └── img/
│
├── instance/                 # 放置不進入版控的環境變數或資料庫
│   └── database.db           # SQLite 資料庫檔案
│
├── docs/                     # 專案說明文件
│   ├── PRD.md                # 產品需求文件
│   └── ARCHITECTURE.md       # 系統架構文件 (本文件)
│
├── requirements.txt          # Python 依賴套件清單
├── .gitignore                # Git 忽略設定
└── app.py                    # 專案啟動入口檔案
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

以下展示使用者與系統互動時，各元件間的資料流向關係：

```mermaid
sequenceDiagram
    participant Browser as 瀏覽器 (使用者)
    participant Route as Flask Route (Controller)
    participant Model as Database Model
    participant SQLite as SQLite 資料庫
    participant Template as Jinja2 Template (View)

    %% 讀取即時狀態列表流程
    Browser->>Route: 1. GET / (請求首頁)
    Route->>Model: 2. 查詢各地點最新回報狀態
    Model->>SQLite: 3. 執行 SELECT 語法
    SQLite-->>Model: 4. 回傳資料
    Model-->>Route: 5. 回傳資料物件
    Route->>Template: 6. 傳遞資料給 index.html 渲染
    Template-->>Browser: 7. 回傳完整 HTML 頁面

    %% 三秒極簡回報流程
    Browser->>Route: A. POST /report (送出體感標籤與座標)
    Route->>Model: B. 建立新回報紀錄 (含時間地點)
    Model->>SQLite: C. 執行 INSERT 語法
    SQLite-->>Model: D. 寫入成功
    Model-->>Route: E. 成功回應
    Route-->>Browser: F. 重新導向至首頁或更新狀態
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

1. **不採用前後端分離架構**
   - **原因**：為了加速 MVP 開發，我們決定讓 Flask 統包後端邏輯與畫面渲染（SSR）。相較於建立一套獨立的 RESTful API 與獨立的 React 專案，Jinja2 讓資料能直接在頁面上顯示，減少跨來源請求 (CORS) 與狀態管理的複雜度。
2. **地理位置 (Geolocation) 獲取交由前端處理**
   - **原因**：使用者的確切經緯度必須由瀏覽器透過 `navigator.geolocation` API 取得並經過使用者同意。因此，回報按鈕點擊後，會先由前端 JS 獲取位置，再將資料與標籤一併以 POST 發送給後端。
3. **輕量級的防刷機制**
   - **原因**：為了防止惡意灌水，系統需記錄使用者的回報行為。初期為了降低使用門檻，我們不強制要求註冊登入，而是使用 Session 或 Cookie 來標記使用者，結合後端邏輯限制「同一使用者 5 分鐘內不可對同一地點重複回報」。
4. **狀態時效性的實作方式**
   - **原因**：為了確保資訊的「即時性」，資料庫會完整記錄每筆回報的時間戳記（Timestamp）。在查詢狀態時，後端只抓取特定時間內（如 1 小時內）的回報資料，或在前端顯示時計算「X 分鐘前」，以確保過時的資訊不會誤導使用者。
1. **SSR 與非同步更新（AJAX）的混搭應用**
   - **原因**：頁面的初次載入由 Flask + Jinja2 處理（SSR），開發快速且利於 SEO。但在「點擊按鈕標註狀態」時，為提供流暢的手機端體驗，會使用 JavaScript 的 Fetch API 傳送請求，讓按鈕的狀態能即時改變而無需重新整理整個網頁。
2. **狀態時效性的被動更新（Lazy Evaluation）**
   - **原因**：PRD 要求狀態過期（如 30 分鐘後）需自動失效。比起在背景執行定時任務（Cron Job）定期掃描資料庫（設定較複雜），系統會採用「被動計算」：當使用者載入列表時，程式若發現某設備最後一筆狀態的時間已超過 30 分鐘，就自動在畫面上將其顯示為「可用 / 預設狀態」，大幅降低後端實作負擔。
3. **資料庫拆分「設備表」與「狀態紀錄表」**
   - **原因**：若只在設備表中存放「當前狀態」，將無法進行歷史分析。拆分出獨立的狀態紀錄表，不僅能透過關聯查詢最新狀態，還能完整保存所有變更軌跡，滿足 PRD 中「歷史統計儀表板」的需求（統計哪些區域長期處於設備維修或大排長龍的狀態）。
4. **輕量化的無登入標註機制**
   - **原因**：為了鼓勵學生隨手回報，MVP 階段不強制註冊與登入。系統可先運用瀏覽器 Session/Cookie 搭配後端的簡單 IP 頻率限制來防止惡意洗版，減少使用者參與回報的第一道門檻。
