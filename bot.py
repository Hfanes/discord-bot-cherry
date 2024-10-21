import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.api_utils import command_get_price, command_nft_price, fetch_coingecko_ids, fetch_nft_collections, get_coingecko_crypto_price, get_crypto_price, fetch_chart, get_logo
from utils.channel_utils import update_channel, plotFunction, embedFunction
from utils.database import create_connection, create_tables
import asyncio
from discord import app_commands
import typing


load_dotenv()
TOKEN = os.getenv('OL')
coins_100_ids = []
collections_nft = {}
intents = discord.Intents.all()
intents.guilds = True  # Enable guilds intent
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    #await setup_data()
    #asyncio.run(create_tables())
    #change_channel_name_loop.start()
    await asyncio.sleep(80)
    await bot.tree.sync()
    

async def setup_data():
    global coins_100_ids, collections_nft
    coins_100_ids = await fetch_coingecko_ids()
    collections_nft = await fetch_nft_collections()

#create channel
@bot.command()
async def test(ctx, crypto_symbol):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name="$$$")
    voice_channel = await guild.create_voice_channel(crypto_symbol,category=category)
    if crypto_symbol.lower() == "solana":
        price = await get_crypto_price(crypto_symbol)
        await ctx.send(f'Voice channel created for {crypto_symbol}!')
    else:
        price = await get_coingecko_crypto_price(crypto_symbol)
    await voice_channel.edit(name=f"{crypto_symbol}: ${price}")
    print(f'Voice channel created for {crypto_symbol}!')


@bot.command()
async def crypto_chart(ctx, crypto, time_frame=30):
    data = await fetch_chart(crypto, time_frame)
    if not data:
        await ctx.send(f"Error with {crypto}. Please try again later.")
        return
    await plotFunction(crypto, data, time_frame)
    _embed, _file = await embedFunction(crypto, time_frame)
    await ctx.send(embed=_embed,file=_file, view = MyView(crypto))


class MyView(discord.ui.View):
    def __init__(self, crypto):
        super().__init__()
        self.crypto = crypto
    @discord.ui.button(label="Reload", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def reload_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.reload_chart(interaction, self.crypto)

    @discord.ui.button(label="7d", style=discord.ButtonStyle.secondary, emoji="📅")
    async def reload__7d_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.reload_chart(interaction, self.crypto, time_frame=7)

    @discord.ui.button(label="30d", style=discord.ButtonStyle.secondary, emoji="📅")
    async def reload_30d_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.reload_chart(interaction, self.crypto, time_frame=30)

    #reload
    async def reload_chart(self, interaction: discord.Interaction, crypto, time_frame=30):
        #More than 3 seconds
        await interaction.response.defer()
        data = await fetch_chart(crypto, time_frame)
        if not data:  # Check if data fetching failed
            await interaction.followup.send(f"Error with {crypto}. Please try again later.")
            return
        await plotFunction(crypto, data, time_frame)
        _embed, _file = await embedFunction(crypto, time_frame)
        await interaction.edit_original_response(embed=_embed, attachments=[_file], view=self)



# @bot.tree.command(description="Create VC price", name="create")
# async def create(interaction: discord.Interaction, channel_name: str, crypto_symbol: str, platform: str):
#     guild = interaction.guild
#     try:
#         voice_channel = await guild.create_voice_channel(channel_name)
        
#         # Insert in db
#         await insert_server_channel(guild.id, voice_channel.id, crypto_symbol, platform, guild.name)
        
#         price = await get_crypto_price(crypto_symbol)
#         await voice_channel.edit(name=f"{crypto_symbol}: ${price}")
#         await interaction.response.send_message(f'Voice channel "{channel_name}" created for {crypto_symbol}!')
#     except Exception as e:
#         print(f"Error: {e}")
#         await interaction.response.send_message("Failed to create voice channel")

#SELECT * FROM users WHERE id = 12345; DROP TABLE servers; -- 
#vs
#SELECT * FROM users WHERE id = '12345; DROP TABLE servers; --'
async def insert_server_channel(server_id: int, channel_id: int, crypto_symbol: str, server_name: str):
    conn = await create_connection()
    try:
        # Check if the server already exists
        server_exists_query = "SELECT id FROM servers WHERE id = $1"
        result = await conn.fetchrow(server_exists_query, server_id)

        if not result:
            # If the server does not exist, insert it
            insert_server_query = "INSERT INTO servers (id, name) VALUES ($1, $2)"
            await conn.execute(insert_server_query, server_id, server_name)

        # Now, insert the channel info
        insert_channel_query = """
            INSERT INTO channels (server_id, channel_id, crypto_symbol, platform) 
            VALUES ($1, $2, $3, $4)
        """
        await conn.execute(insert_channel_query, server_id, channel_id, crypto_symbol)
    finally:
        await conn.close()

    

@tasks.loop(seconds=840)
async def change_channel_name_loop():
    # Connect to the database
    conn = await create_connection()
    try:
        # Retrieve all servers and associated channels
        channels = await conn.fetch("SELECT channel_id, crypto_symbol FROM channels")

        # Create a dictionary to hold channel price updates
        price_updates = {}
        
        # Fetch current prices for each cryptocurrency only once
        for row in channels:
            channel_id = row['channel_id']
            crypto_symbol = row['crypto_symbol']
            
            # Use a single API call to fetch the current price
            current_price = await get_crypto_price(crypto_symbol)
            if current_price is not None:
                price_updates[channel_id] = current_price

        # Update channel names in Discord
        for channel_id, current_price in price_updates.items():
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.edit(name=f"{channel.name.split(' - ')[0]} - ${current_price}")  # Retain channel base name
    except Exception as e:
        print(f"Error updating channel names: {e}")
    finally:
        await conn.close()


        
@bot.tree.command(description="Coin price", name="price")
async def price(interaction: discord.Interaction, symbol: str):
    symbol = symbol.lower()
    try:
        value = await get_coingecko_crypto_price(symbol)
        await interaction.response.send_message(f"Preço de {symbol}: {value}$")
    except Exception:
        interaction.response.send_message(f"You need the API ID - coingecko website")
        return
    
@price.autocomplete("id")
async def coin_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_ids = []
    for id_choice in coins_100_ids:
     if current.lower() in id_choice.lower():
        filtered_ids.append(id_choice)
    choices = [
        app_commands.Choice[str](name=id_choice, value=id_choice) 
        for id_choice in filtered_ids[:25]
    ]
    return choices
    
@bot.tree.command(description="Nft price top 100", name="nft")
async def nft(interaction: discord.Interaction, nft: str):
    nft = nft.lower()
    nft_id = None
    for id_, name in collections_nft.items():
        if name.lower() == nft:
            nft_id = id_
            break
    if nft_id:
        value = await command_nft_price(nft_id)
        await interaction.response.send_message(f"Preço de {nft}: {value} SOL")
    
@nft.autocomplete("nft")
async def nft_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_nft = []
    for nft_id, nft_name in collections_nft.items():
     if current.lower() in nft_name.lower():
        filtered_nft.append(nft_name)
    choicesnft = [
        app_commands.Choice[str](name=nft_name, value=nft_name) 
        for nft_name in filtered_nft[:25]
    ]
    return choicesnft

bot.run(TOKEN)