# test-connection.py - FIXED
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text  # ✅ Import text


async def test_connection():
    try:
        engine = create_async_engine(
            "postgresql+asyncpg://booking_user:booking_pass@localhost:5432/booking_db", echo=True
        )

        async with engine.connect() as conn:
            # ✅ Use text() to wrap SQL
            result = await conn.execute(text("SELECT 1"))
            print("✅ Connection successful!")
            print(f"Result: {result.scalar()}")

        await engine.dispose()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_connection())
