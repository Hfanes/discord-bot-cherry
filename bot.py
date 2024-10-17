import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.api_utils import command_get_price, command_nft_price, fetch_coingecko_ids, fetch_nft_collections, get_coingecko_crypto_price, get_crypto_price, fetch_chart, get_logo
from utils.channel_utils import update_channel
from utils.database import create_connection, create_tables
import asyncio
from discord import app_commands
import typing
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from PIL import Image
from io import BytesIO
import requests

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


@bot.command()
async def test(ctx, crypto_symbol):
    guild = ctx.guild
    voice_channel = await guild.create_voice_channel(crypto_symbol)
    if crypto_symbol.lower() == "solana":
        price = await get_crypto_price(5426)
        await ctx.send(f'Voice channel created for {crypto_symbol}!')
    else:
        price = await get_coingecko_crypto_price(crypto_symbol)
    await voice_channel.edit(name=f"{crypto_symbol}: ${price}")
    print(f'Voice channel created for {crypto_symbol}!')

@bot.command()
async def crypto_chart(ctx, crypto):
    data = await fetch_chart(crypto)
    values = data['prices']
    timestamps = [datetime.fromtimestamp(value[0] / 1000) for value in values]
    values_prices = [value[1] for value in values]
    # Create the chart
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='#252e33')
    #colors
    ax.plot(timestamps, values_prices, label=crypto.capitalize(), color="#ff9904")
    ax.tick_params(axis='both', which='major', labelsize=6, color="#ffff")  # Set tick 
    ax.grid(True, color='#121719', linestyle='-', linewidth=0.5)  #grid line color
    ax.set_facecolor('#252e33')  # Set the axes background color

    ax.set_title(f'{crypto.capitalize()} Price Chart', color='white')  # Set title color to contrast
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))  # Format: 16 Oct 2024
    plt.xticks(rotation=45)
    plt.tight_layout()# Use tight layout to help center and adjust spacing
    #logo
    
    logo, name = await get_logo(crypto)
    print(name)
    if logo:
        # Download the logo image
        response = requests.get(logo)        
        #save in memory and convert to rgba bc of colors
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        # Get the dimensions of the logo image
        logo_width, logo_height = img.size
        #center position
        fig_width, fig_height = fig.get_size_inches() * fig.dpi  # Get figure size in pixels
        center_x = (fig_width - logo_width) / 2
        center_y = (fig_height - logo_height) / 2
        # Add the image to the figure as a watermark
        fig.figimage(img, xo=center_x, yo=center_y, alpha=0.4, zorder=1)
    plt.savefig('crypto_chart.png', facecolor='#252e33')  # Save with the figure's facecolor
    plt.close()
    #await ctx.send(file=discord.File('crypto_chart.png'))

    embed=discord.Embed(title=" ")
    embed.set_author(name="Bitcoin (BTC) in EUR", url="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png", icon_url="https://s2.coinmarketcap.com/static/img/coins/64x64/1.png")
    embed.add_field(name="Price", value="€62141.4", inline=True)
    embed.add_field(name="Highest in 24h", value="€62697.1", inline=True)
    embed.add_field(name="Lowest in 24h", value="€60698.9", inline=True)
    embed.add_field(name="Change in 1h", value="-0.49%", inline=True)
    embed.add_field(name="Change in 24h", value="+1.95%", inline=True)
    embed.add_field(name="Change in 7d", value="+11.98%", inline=True)
    embed.set_footer(text="with love to cherry crew🍒")
    embed=discord.Embed(color=0xA90101)
    file = discord.File("./crypto_chart.png", filename='crypto_chart.png')
    embed.set_image(url='attachment://crypto_chart.png')
    await ctx.send(embed=embed,file=file)



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
async def price(interaction: discord.Interaction, id: str):
    id = id.lower()
    try:
        value = await command_get_price(id)
        await interaction.response.send_message(f"Preço de {id}: {value}$")
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