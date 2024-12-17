import asyncpg
from config.settings import DATABASE_URL

async def create_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL, ssl="require")
        print("success"+ str(conn))
        return conn 
    except Exception as e:
        print("error" + str(e))
        return None

async def run_migrations():
    try:
        conn = await create_connection()
        await conn.execute("""
            ALTER TABLE channels
                ALTER COLUMN previous_price TYPE DECIMAL(20, 10);
        """)
        print("Column updated successfully!")
        await conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")