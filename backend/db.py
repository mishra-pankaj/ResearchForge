# backend/db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

# pool_pre_ping checks the connection before use, so a restarted
# database doesn't cause errors in the app.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# A session is one unit of work: open, query or write, commit, close.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Parent class for all tables. SQLAlchemy uses it to track them."""
    pass


def get_db():
    """Gives a session to one API request, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()