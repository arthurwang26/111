# [檔案用途：建立預設管理員帳號腳本] (不需更動)
from app.db import SessionLocal
from app.db import User
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            username="admin",
            hashed_password=get_password_hash("123456")
        )
        db.add(admin)
        db.commit()
        print("Admin user created!")
    else:
        print("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    create_admin()
