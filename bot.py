import json
import typing
import aiohttp
import discord
from discord.ext import commands, tasks
import os
import requests
import locale
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from dotenv import load_dotenv
import asyncio
import datetime
from discord import app_commands

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
intentes = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intentes)
previous_price = None
load_dotenv()
Token = os.getenv('OL')
cmc_api_key = os.getenv('CMC_API_KEY')
simple_api_key = os.getenv('simple_api_key')

response = requests.get("https://api.coingecko.com/api/v3/coins/list")
if response.status_code == 200:
    data = response.json()
    ids = [item['id'] for item in data]

nfturl = "https://api.simplehash.com/api/v0/nfts/collections/top_v2?chains=solana&time_period=24h&limit=100"
headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
responsenft = requests.get(nfturl, headers=headers)
if responsenft.status_code == 200:
    data = responsenft.json()
    collections_dict = {}
    for collection in data["collections"]:
        collection_details = collection.get("collection_details", {})
        if collection_details:
            name = collection_details.get("name")
            collection_id = collection_details.get("collection_id")
            collections_dict[collection_id] = name
    #print(collections_dict)

 

cryptosCMC = {
    'solana': {'id': 5426, 'channel_id': int(os.getenv('SOL')), 'previous_price': None},
    'ethereum': {'id': 1027, 'channel_id': int(os.getenv('ETH')), 'previous_price': None},
    'bitcoin': {'id': 1, 'channel_id': int(os.getenv('BTC')), 'previous_price': None},
}

cryptosCG = {
    'rune': {'symbol': 'thorchain','channel_id': int(os.getenv('RUNE')), 'previous_price': None},
    'doge': {'symbol': 'dogecoin','channel_id': int(os.getenv('DOGE')), 'previous_price': None},
    'ada': { 'symbol': 'cardano','channel_id': int(os.getenv('ADA')), 'previous_price': None},
    'w' : { 'symbol': 'wormhole','channel_id': int(os.getenv('W')), 'previous_price': None},
    'wif' : { 'symbol': 'dogwifcoin','channel_id': int(os.getenv('WIF')), 'previous_price': None},
    'jup' : { 'symbol': 'jupiter-exchange-solana','channel_id': int(os.getenv('JUP')), 'previous_price': None},
}



@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    change_channel_name_loop.start()
    await asyncio.sleep(80)
    await bot.tree.sync()
    
 
@bot.tree.command(name= "sync", description="to sync")
async def sync (interaction: discord.Interaction):
    await interaction.response.send_message("Syncing...")
    await bot.tree.sync()
    print("Synced")


@bot.tree.command(description="Coin price", name="price")
async def price(interaction: discord.Interaction, id: str):
    id = id.lower()
    try:
        value = await command_get_price(id)
        await interaction.response.send_message(f"Preço de {id}: {value}$")
    except Exception:
        interaction.response.send_message(f"É preciso do API ID encontrado ná pagina da coin no site coingecko")
        return
    
@price.autocomplete("id")
async def coin_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_ids = []
    for id_choice in ids:
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
    for id_, name in collections_dict.items():
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
    for nft_id, nft_name in collections_dict.items():
     if current.lower() in nft_name.lower():
        filtered_nft.append(nft_name)
    choicesnft = [
        app_commands.Choice[str](name=nft_name, value=nft_name) 
        for nft_name in filtered_nft[:25]
    ]
    return choicesnft

@tasks.loop(seconds=840)
async def change_channel_name_loop():
    for crypto, info in cryptosCMC.items():
        current_price = get_crypto_price(info['id'])
        await update_channel(info['channel_id'], info['previous_price'], current_price, "", crypto.upper())
        info['previous_price'] = current_price

    for crypto, info in cryptosCG.items():
        current_price = get_coingecko_crypto_price(info['symbol'])
        await update_channel(info['channel_id'], info['previous_price'], current_price, "", crypto.upper())
        info['previous_price'] = current_price
        await asyncio.sleep(10)
    channel = bot.get_channel(1080342658901364777)
    await channel.send(content="Preços atualizados")
         

async def update_channel(channel_id, previous_price, crypto_price, emoji, symbol):
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            if previous_price is not None:
                if crypto_price > previous_price:
                    emoji = "🟢"
                elif crypto_price < previous_price:
                    emoji = "🔴"

            new_channel_name = f"{emoji}{symbol}: ${crypto_price}"

            if isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=new_channel_name)
                print(f"Nome do canal de voz alterado para: {new_channel_name}")
            else:
                print("Canal não é um canal de voz.")
            previous_price = crypto_price
        except Exception as e:
            print(f"Erro ao obter dados do preço: {e}")
    else:
        print("Canal não encontrado.")

def get_crypto_price(id):
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {'id': id}
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': cmc_api_key,
    }
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        response_json = response.json()
        crypto_price = response_json['data'][str(id)]['quote']['USD']['price']
        formatted_crypto_price = "{:.2f}".format(crypto_price)
        print(formatted_crypto_price)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    return formatted_crypto_price


def get_coingecko_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    try:
        response = requests.get(url)
        response_json = response.json()
        if symbol in response_json and "usd" in response_json[symbol]:
            res = response_json[symbol]["usd"]
            formatted_price = "{:.3f}".format(res)
            return formatted_price            
        else:
            print(f"Erro no symbol: {symbol}")
            return None
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        return None
    
async def command_get_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_json = await response.json()
                if symbol in response_json and "usd" in response_json[symbol]:
                    res = response_json[symbol]["usd"]
                    formatted_price = "{:.3f}".format(res)
                    return formatted_price
                else:
                    print(f"Error in symbol: {symbol}")
                    return None
    except aiohttp.ClientError as e:
        print(e)
        return None

async def command_nft_price(nftid):
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    today = datetime.date.today().isoformat()
    url = f"https://api.simplehash.com/api/v0/nfts/floor_prices_v2/collection/{nftid}/daily?marketplace_ids=tensor&start_date={today}"   
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response_json = await response.json()
            pricelamp = response_json["floor_prices"][0]["floor_price"]
            price = pricelamp / 1000000000
            return price


    
bot.run(Token)