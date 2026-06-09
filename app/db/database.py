from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import DB_URL

engine = create_engine(DB_URL)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_database_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()