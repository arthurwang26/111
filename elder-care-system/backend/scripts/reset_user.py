import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import User, Base
from passlib.context import CryptContext

engine = create_engine('sqlite:///./elder_care_v2.db')
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)()

pwd = CryptContext(schemes=['bcrypt']).hash('arthur')
Session.query(User).delete()
Session.add(User(username='arthur', hashed_password=pwd))
Session.commit()
Session.close()
print('Done: arthur / arthur')
