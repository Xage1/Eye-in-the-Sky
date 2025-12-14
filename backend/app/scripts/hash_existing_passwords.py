# backend/app/scripts/hash_existing_passwords.py
import asyncio
from app.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.utils.security import hash_password

async def run():
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        updated = 0
        for u in users:
            pwd = getattr(u, "password", None)
            if not pwd:
                continue
            # skip if it already looks like a bcrypt hash ($2b$ or $2a$ prefix)
            if isinstance(pwd, str) and (pwd.startswith("$2a$") or pwd.startswith("$2b$") or pwd.startswith("$2y$")):
                continue
            hashed = hash_password(str(pwd))
            u.password = hashed
            session.add(u)
            updated += 1
        await session.commit()
        print(f"Updated {updated} users with hashed passwords.")

if __name__ == "__main__":
    asyncio.run(run())