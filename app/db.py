from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


engine = create_async_engine("sqlite+aiosqlite:///./payments.db", echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session