"""Test backend database and API"""
import sys
sys.path.insert(0, '/home/free33/dev/1st4-mobile')
import asyncio

async def test():
    from backend.database import init_db, get_db
    from backend.models import Client
    
    await init_db()
    print('Database tables created ok')
    
    async for session in get_db():
        count = await session.scalar(Client.count())
        if count is None:
            # SQLAlchemy might return this differently
            from sqlalchemy import select, func
            result = await session.execute(select(func.count(Client.id)))
            count = result.scalar()
        print(f'Client count: {count}')
        break

asyncio.run(test())
print('ALL OK')
