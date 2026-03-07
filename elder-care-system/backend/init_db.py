# [檔案用途：初始化空資料庫腳本] (不需更動)
from app.db import engine
from app.db import Base

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()
