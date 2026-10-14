from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists

from app.config import DEFAULT_TARIFFS
from app.models import Tariff


async def seed_tariffs(
        session: AsyncSession
):
    for current_tariff, price in DEFAULT_TARIFFS.items():
        tariff_query = select(Tariff.id).where(Tariff.title == current_tariff)
        if not await session.scalar(select(tariff_query.exists())):
            session.add(Tariff(title=current_tariff, price=price))

    await session.commit()

