from app.core.security import verify_password
from app.db.database import SessionLocal
from app.db.models import User

def check_testadmin():
    db = SessionLocal()
    u = db.query(User).filter(User.username == "testadmin").first()
    if u:
        print(f"User: {u.username}")
        print(f"Verify 'password123': {verify_password('password123', u.hashed_password)}")
    else:
        print("testadmin not found")
    db.close()

if __name__ == "__main__":
    check_testadmin()
