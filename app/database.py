from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings  # Import settings from config.py

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
