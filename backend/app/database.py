from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
enigne = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(enigne, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base