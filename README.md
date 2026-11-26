# 郵局網站（Django 骨架）

Django 6.1 + Neon PostgreSQL 的全端網站骨架。目前包含：

- 自訂會員模型（`apps.accounts.User`）
- 註冊 / 登入 / 登出
- 登入會員資料表（`user`: id、帳號、密碼、電話、名字、組別）與包裹追蹤資料表（`parcel`）
- Tailwind CSS（CDN，免建置）
- Neon 連線設定（未設定時自動退回 SQLite）

---

## 快速開始

```powershell
# 1. 建立虛擬環境（已存在可跳過）
python -m venv .venv

# 2. 安裝套件
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. 環境變數
copy .env.example .env
# 打開 .env，至少改掉 SECRET_KEY

# 4. 建立登入、包裹與儲匯等候資料表
.venv\Scripts\python.exe manage.py setup_user_table
.venv\Scripts\python.exe manage.py setup_parcel_table
.venv\Scripts\python.exe manage.py setup_remittance_queue_table
.venv\Scripts\python.exe manage.py setup_feedback_table
.venv\Scripts\python.exe manage.py setup_user_operation_log_table

# 5. 啟動
.venv\Scripts\python.exe manage.py runserver
```

開啟：

| 網址 | 內容 |
| --- | --- |
| <http://127.0.0.1:8000/> | 首頁 |
| <http://127.0.0.1:8000/accounts/register/> | 註冊 |
| <http://127.0.0.1:8000/accounts/login/> | 登入 |
| <http://127.0.0.1:8000/health> | 健康檢查（回 200 JSON） |

---

## 連接 Neon PostgreSQL

本專案已連結 Neon `production` branch。Neon CLI 會將 pooled `DATABASE_URL` 和 direct `DATABASE_URL_UNPOOLED` 寫入根目錄 `.env`；網站日常使用 pooled URL，資料表初始化使用 direct URL。

建立新的 Neon 專案時，可先安裝 Neon CLI、登入，再於專案根目錄執行：

Neon CLI 初始化後，使用 direct connection 建立登入與包裹表：

```powershell
$line = Get-Content .env | Where-Object { $_ -match '^DATABASE_URL_UNPOOLED=' } | Select-Object -First 1
$env:DATABASE_URL = $line.Substring('DATABASE_URL_UNPOOLED='.Length).Trim('"')
.venv\Scripts\python.exe manage.py setup_user_table
.venv\Scripts\python.exe manage.py setup_parcel_table
.venv\Scripts\python.exe manage.py setup_remittance_queue_table
.venv\Scripts\python.exe manage.py setup_feedback_table
.venv\Scripts\python.exe manage.py setup_user_operation_log_table
Remove-Item Env:DATABASE_URL
```

此專案刻意不建立 `django_migrations`、`django_session`、權限或管理後台資料表。登入 session 使用簽章 Cookie。不要執行 `manage.py migrate` 或 `createsuperuser`，以免 Django 建立其他資料表；目前由專用的 `setup_*_table` 指令初始化資料表。新版意見回饋存於 `userfeedback`，會關聯會員並保存提交時帳號名稱、按讚／倒讚／意見表單類型、內容、選填聯絡方式與時間；執行 `setup_feedback_table` 建立新版資料表。舊版 `feedback` 表不會由此指令刪除。登入會員使用網站功能時，操作名稱、帳號、時間與頁面前景停留秒數會記錄於 `useroperationlog`；執行 `setup_user_operation_log_table` 建立或補齊該表，管理後台可查看使用次數、停留時間與最近 200 筆紀錄。儲匯等候人數存於 `remittancequeue`，取號紀錄存於 `remittanceticket`。執行 `setup_remittance_queue_table` 會建立或補齊這兩張資料表及業務類別欄位，並補上初始示範資料，不會覆寫既有等候人數。一般業務取號分為匯款、存提、開戶、換印鑑，另有郵務業務取號；同一帳號在同一郵局可依不同業務各取一張號碼牌。新取號會讓該郵局等候人數加一，同業務重複取號會顯示原號碼，不會重複加人。頁面預估時間依每位等候者 2 分鐘計算。查詢頁預放 `DEMO-` 示範包裹，狀態與位置尚未串接中華郵政即時物流資料。

更新郵局等候人數時可執行：

```powershell
.venv\Scripts\python.exe manage.py update_remittance_waiting "臺北北門郵局" 8
```

注意事項：

- 網站請求使用 **pooled**（主機名稱含 `-pooler`）連線；schema migration、`pg_dump` 等管理工作使用 **direct** 連線。
- `config/settings/base.py` 已自動設定 `ssl_require=True` 與 `DISABLE_SERVER_SIDE_CURSORS = True`（Neon 的 PgBouncer transaction mode 必要）。
- Neon 免費方案會休眠，第一次請求會有 0.5～2 秒冷啟動。
- 建議用 Neon 的 **branch** 區分環境：`main`（正式）、`dev`（開發）。
- `.env` 不要進 git。

---

## 專案結構

```text
UI_Design/
├── config/
│   ├── settings/
│   │   ├── base.py      # 共用設定、資料庫、認證
│   │   ├── dev.py       # 本機開發（DEBUG=True）
│   │   └── prod.py      # 正式環境（安全設定、Whitenoise manifest）
│   └── urls.py
├── apps/
│   ├── accounts/      # 自訂 User、註冊 / 登入
│   └── core/          # 首頁；之後放最新消息、業務、據點
├── templates/
│   ├── base.html
│   ├── home.html
│   └── accounts/
└── static/css/style.css
```

---

## 常用指令

```powershell
# 套用模型變更
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate

# 收集靜態檔（部署前）
.venv\Scripts\python.exe manage.py collectstatic

# 部署前檢查
.venv\Scripts\python.exe manage.py check --deploy --settings=config.settings.prod
```

---

## 開發約定

- 新增功能一律開一個 app：`.venv\Scripts\python.exe manage.py startapp <name> apps\<name>`，
  並把 `apps.py` 的 `name` 改成 `apps.<name>`、加上 `label`。
- 新 app 要加進 `config/settings/base.py` 的 `INSTALLED_APPS`。
- 會員相關欄位加在 `apps/accounts/models.py` 的 `User`。
- 樣式優先用 Tailwind class；Django 表單元件的基礎樣式在 `static/css/style.css`。

---

## 之後可以加

- `django-unfold`：美化後台
- `django-import-export`：後台匯入 / 匯出 Excel
- 最新消息 / 業務項目 / 據點查詢的 model 與頁面
- 聯絡表單（存 DB + 通知信）
- 部署（Render / Railway）+ Cloudflare R2 存上傳檔
