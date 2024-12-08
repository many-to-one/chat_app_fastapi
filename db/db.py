from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from dotenv import load_dotenv
import os

load_dotenv()


Base = declarative_base()

async_engine = create_async_engine(os.getenv("DATABASE_URL"), echo=True)
async_session = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

async def get_db():
    async with async_session() as session:
        yield session
