import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.api_utils import command_get_price, command_nft_price, fetch_coingecko_ids, fetch_nft_collections, get_coingecko_crypto_price, get_crypto_price
from utils.channel_utils import update_channel
import asyncio
from discord import app_commands
import typing

load_dotenv()
TOKEN = os.getenv('OL')
coins_100_ids = []
collections_nft = {}
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)



cryptosCMC = {
    'solana': {'id': 5426, 'channel_id': int(os.getenv('SOL')), 'previous_price': None},
    'ethereum': {'id': 1027, 'channel_id': int(os.getenv('ETH')), 'previous_price': None},
    'bitcoin': {'id': 1, 'channel_id': int(os.getenv('BTC')), 'previous_price': None},
}

cryptosCG = {
    'rune': {'symbol': 'thorchain','channel_id': int(os.getenv('RUNE')), 'previous_price': None},
    'doge': {'symbol': 'dogecoin','channel_id': int(os.getenv('DOGE')), 'previous_price': None},
    'w' : { 'symbol': 'wormhole','channel_id': int(os.getenv('W')), 'previous_price': None},
    'wif' : { 'symbol': 'dogwifcoin','channel_id': int(os.getenv('WIF')), 'previous_price': None},
    'jup' : { 'symbol': 'jupiter-exchange-solana','channel_id': int(os.getenv('JUP')), 'previous_price': None},
}


@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    await setup_data()
    change_channel_name_loop.start()
    await asyncio.sleep(80)
    await bot.tree.sync()

async def setup_data():
    global coins_100_ids, collections_nft
    coins_100_ids = await fetch_coingecko_ids()
    collections_nft = await fetch_nft_collections()


@tasks.loop(seconds=840)
async def change_channel_name_loop():
    for crypto, info in cryptosCMC.items():
        current_price = await get_crypto_price(info['id'])
        if current_price is None:
            continue
        await update_channel(bot, info['channel_id'], info['previous_price'], current_price, "", crypto.upper())
        info['previous_price'] = current_price

    for crypto, info in cryptosCG.items():
        current_price = await get_coingecko_crypto_price(info['symbol'])
        if current_price is None:
            continue
        await update_channel(bot, info['channel_id'], info['previous_price'], current_price, "", crypto.upper())
        info['previous_price'] = current_price
        await asyncio.sleep(10)

@bot.tree.command(description="Create VC price", name="create")
async def create(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild
    try:
        voice_channel = await guild.create_voice_channel(channel_name)
        await interaction.send(f'Voice channel "{channel_name}" created!')
    except Exception:
        interaction.response.send_message("Failed to create voice channel")
        return

        
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