from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import DATABASE_URL, SQL_ECHO


engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
