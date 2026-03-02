from app.core.security import verify_password, get_password_hash
from app.db.database import SessionLocal
from app.db.models import User

def check_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        print("Admin user not found!")
        return
    
    password_to_check = "123456"
    is_correct = verify_password(password_to_check, admin.hashed_password)
    
    print(f"Checking for user: {admin.username}")
    print(f"Hash in DB: {admin.hashed_password}")
    print(f"Verification of '123456': {is_correct}")

    # Also test creating a NEW hash and verifying it
    new_hash = get_password_hash("test123")
    print(f"New test hash for 'test123': {new_hash}")
    print(f"Verification of 'test123': {verify_password('test123', new_hash)}")
    
    db.close()

if __name__ == "__main__":
    check_admin()
