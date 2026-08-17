from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "postgresql+psycopg://..."

engine = create_engine(DATABASE_URL)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)
