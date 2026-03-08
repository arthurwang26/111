import os

HEADERS = {
    "app/main.py": "# [檔案用途：系統啟動入口管理] (預設不需更動，全系統的核心啟動點)\n",
    "app/api/auth.py": "# [檔案用途：身份驗證與登入 API] (不需更動)\n",
    "app/api/dashboard.py": "# [檔案用途：首頁儀表板資料 API] (不需更動)\n",
    "app/api/elders.py": "# [檔案用途：長者資料管理(CRUD) API] (不需更動)\n",
    "app/api/schemas.py": "# [檔案用途：資料傳輸格式定義 Pydantic Models] (若增減欄位可改)\n",
    "app/api/video.py": "# [檔案用途：即時影像串流 API] (不需更動)\n",
    "app/cv/processor.py": "# [檔案用途：核心 AI 處理與姿勢辨識] (⭐️負責辨識的兩位同學請專注修改此檔案⭐️ 可以自由調整跌倒判斷邏輯和閾值)\n",
    "app/db/database.py": "# [檔案用途：資料庫連線設定 Engine] (請勿更動)\n",
    "app/db/models.py": "# [檔案用途：資料表結構定義 SQLAlchemy] (若需新增資料庫欄位可改)\n",
    "app/core/security.py": "# [檔案用途：密碼雜湊與權杖加密 JWT] (請勿更動)\n",
    "app/services/line_notify.py": "# [檔案用途：LINE Notify 通知推送邏輯] (⭐️負責通知推送的同學請專注修改此檔案⭐️)\n",
    "app/services/baseline_worker.py": "# [檔案用途：長者日常作息基準線背景任務] (處理誤報邏輯可改)\n",
    "init_db.py": "# [檔案用途：初始化空資料庫腳本] (不需更動)\n",
    "create_admin.py": "# [檔案用途：建立預設管理員帳號腳本] (不需更動)\n",
    "download_models.py": "# [檔案用途：下載預訓練 AI 模組腳本] (不需更動)\n"
}

def prepend_header(filepath, header):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("# [檔案用途"):
        return # already added
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content)

for path, header in HEADERS.items():
    prepend_header(path, header)

# Cleanup unused test scripts
files_to_delete = [
    "check_testadmin.py", "reset_admin.py", "create_test_user.py", 
    "test_app.py", "test_auth.py", "test_rtsp_connection.py"
]

for f in files_to_delete:
    if os.path.exists(f):
        os.remove(f)

print("Cleanup and documentation headers injection complete!")
