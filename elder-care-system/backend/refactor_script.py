import os
import shutil

backend_dir = r"c:\Users\arthu\Desktop\1111\111\elder-care-system\backend"
app_dir = os.path.join(backend_dir, "app")

# 1. Merge db/database.py and db/models.py
db_dir = os.path.join(app_dir, "db")
db_py_path = os.path.join(app_dir, "db.py")

with open(os.path.join(db_dir, "database.py"), "r", encoding="utf-8") as f:
    db_content = f.read()
with open(os.path.join(db_dir, "models.py"), "r", encoding="utf-8") as f:
    models_content = f.read()

models_content = models_content.replace("from .database import Base\n", "")

merged_db = db_content + "\n" + models_content
with open(db_py_path, "w", encoding="utf-8") as f:
    f.write(merged_db)

# 2. Merge core/security.py to api/auth.py
core_dir = os.path.join(app_dir, "core")
api_dir = os.path.join(app_dir, "api")
auth_py_path = os.path.join(api_dir, "auth.py")

with open(os.path.join(core_dir, "security.py"), "r", encoding="utf-8") as f:
    sec_content = f.read()
with open(auth_py_path, "r", encoding="utf-8") as f:
    auth_content = f.read()

auth_content = auth_content.replace("from ..core.security import verify_password, get_password_hash, create_access_token, ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES\n", "")
auth_content = auth_content.replace("from ..db.database import get_db\n", "")
auth_content = auth_content.replace("from ..db.models import User\n", "")
auth_content = auth_content.replace("from jose import JWTError, jwt\n", "")
auth_content = auth_content.replace("from datetime import timedelta\n", "")

merged_auth = """# [檔案用途：身份驗證與登入 API] (不需更動)
import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..db import get_db, User
from ..api.schemas import Token, UserCreate, User as UserSchema

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days for convenience
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

""" + "\n".join(auth_content.splitlines()[12:])

with open(auth_py_path, "w", encoding="utf-8") as f:
    f.write(merged_auth)

# 3. Remove old dirs
shutil.rmtree(db_dir)
shutil.rmtree(core_dir)

# 4. Search and Replace imports
def replace_in_file(filepath, old, new):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if old in content:
        new_content = content.replace(old, new)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

for root, _, files in os.walk(backend_dir):
    if "venv" in root or "__pycache__" in root or "alembic" in root: continue
    for file in files:
        if file.endswith(".py") and file != "refactor_script.py":
            path = os.path.join(root, file)
            replace_in_file(path, "from app.db.database import", "from app.db import")
            replace_in_file(path, "from app.db.models import", "from app.db import")
            replace_in_file(path, "from ..db.database import", "from ..db import")
            replace_in_file(path, "from ..db.models import", "from ..db import")
            replace_in_file(path, "from .db.database import", "from .db import")
            replace_in_file(path, "from .db.models import", "from .db import")

replace_in_file(os.path.join(app_dir, "main.py"), "from .db import engine, Base\nfrom .db import models", "from .db import engine, Base")
replace_in_file(os.path.join(app_dir, "main.py"), "models.Base.metadata.create_all(bind=engine)", "Base.metadata.create_all(bind=engine)")

print("Refactoring complete.")
