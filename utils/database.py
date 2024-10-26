import asyncpg
from config.settings import DB_URL

async def create_connection():
    try:
        conn = await asyncpg.connect(DB_URL, ssl="require")
        print("success"+ str(conn))
        return conn 
    except Exception as e:
        print("error" + str(e))
        return None


async def create_tables():
    conn = await create_connection()

    create_servers_table = """
    CREATE TABLE IF NOT EXISTS servers (
        id SERIAL PRIMARY KEY,
        discord_id BIGINT UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL
    );
    """

    create_channels_table = """
    CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        server_id BIGINT REFERENCES servers(discord_id) ON DELETE CASCADE,
        channel_id BIGINT NOT NULL,
        crypto_symbol VARCHAR(10) NOT NULL,
        previous_price DECIMAL(15, 6),
        UNIQUE (server_id, channel_id) -- Ensure a channel is only added once per server
    );
    """
    # create_alerts_table = """
    # CREATE TABLE IF NOT EXISTS alerts (
    #     id SERIAL PRIMARY KEY,
    #     server_id BIGINT REFERENCES servers(discord_id) ON DELETE CASCADE,
    #     crypto_symbol VARCHAR(10) NOT NULL,
    #     alert_price DECIMAL(15, 6) NOT NULL,
    #     is_active BOOLEAN DEFAULT TRUE,
    #     UNIQUE (server_id, crypto_symbol) -- Ensure one alert per crypto per server
    # );
    # """

    await conn.execute(create_servers_table)
    await conn.execute(create_channels_table)
    #await conn.execute(create_alerts_table)

    await conn.close()

