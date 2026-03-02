from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def reset_admin():
    db = SessionLocal()
    # 查找 admin 使用者
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        admin.hashed_password = get_password_hash("123456")
        db.commit()
        print("Admin password has been reset to: 123456")
    else:
        # 如果不存在則建立
        new_admin = User(username="admin", hashed_password=get_password_hash("123456"))
        db.add(new_admin)
        db.commit()
        print("Admin created with password: 123456")
    db.close()

if __name__ == "__main__":
    reset_admin()
