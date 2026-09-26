import asyncio
import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.star import Star

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "stars_catalogue.json"


async def seed_stars():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        catalogue = json.load(f)

    async with AsyncSessionLocal() as session:  # type: AsyncSession
        inserted = 0

        for star in catalogue["stars"]:
            catalog_id = star["id"]

            exists = await session.execute(
                select(Star).where(Star.catalog_id == catalog_id)
            )
            if exists.scalar():
                continue

            record = Star(
                catalog_id=catalog_id,
                proper_name=star["identifiers"]["common_name"]
                or star["identifiers"]["bayer_designation"]
                or f"HR {catalog_id}",
                bayer_designation=star["identifiers"]["bayer_designation"],
                constellation=star["constellation"]["name"] or "Unassigned",
                iau_abbreviation=star["constellation"]["iau_abbreviation"],
                ra=star["coordinates"]["ra"],
                dec=star["coordinates"]["dec"],
                magnitude=star["photometry"]["visual_magnitude"],
            )

            session.add(record)
            inserted += 1

        await session.commit()
        print(f"🌟 Seeded {inserted} stars")


if __name__ == "__main__":
    asyncio.run(seed_stars())
