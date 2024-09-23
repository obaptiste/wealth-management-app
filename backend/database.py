from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager


load_dotenv()




DATABASE_URL = os.getenv("DATABASE_URL_ASYNC")


engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

@asynccontextmanager
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

Base = declarative_base()