from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def create_test_user():
    db = SessionLocal()
    username = "testadmin"
    password = "password123"
    
    # 確保不存在
    db.query(User).filter(User.username == username).delete()
    
    new_user = User(username=username, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    print(f"Test user created: {username} / {password}")
    db.close()

if __name__ == "__main__":
    create_test_user()
