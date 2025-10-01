import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://user:password@localhost:5432/dbname"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine)