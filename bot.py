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

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
client = commands.Bot(command_prefix="$", intents=discord.Intents.all())
stop = False
previous_price = None
previous_price_jup = None
load_dotenv()
Token = os.getenv('OL')
client = commands.Bot(command_prefix="$", intents=discord.Intents.all())


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
    'dust' : { 'symbol': 'dust-protocol','channel_id': int(os.getenv('DUST')), 'previous_price': None},  
}

cmc_api_key = os.getenv('CMC_API_KEY')
simple_api_key = os.getenv('simple_api_key')

@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    #change_channel_name_loop.start()
    #await asyncio.sleep(61)
    #pricehour.start()
    


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
         

async def update_channel(channel_id, previous_price, crypto_price, emoji, symbol):
    channel = client.get_channel(channel_id)

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


async def get_coingecko_crypto_price(symbol):
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
    
@client.command(name='price')
async def price(ctx, crypto: str):
    crypto = crypto.lower()
    try:
        value = await get_coingecko_crypto_price(crypto)
        await ctx.send(f"Preço de {crypto}: {value}$")
    except Exception:
            print(f"É preciso do API ID encontrado ná pagina da coin no site coingecko")


def dustprice():
  response = requests.get(
      "https://api.coingecko.com/api/v3/coins/dust-protocol?localization=false"
  )
  response_json = response.json()
  dustpricereturn = {
      "priceUSD":
      locale.currency(response_json["market_data"]["current_price"]["usd"]),
      "h24change":
      response_json["market_data"]["price_change_percentage_24h"]
  }
  return dustpricereturn



def degod_price():
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    today = datetime.date.today().isoformat()
    url = f"https://api.simplehash.com/api/v0/nfts/floor_prices_v2/collection/f027e33134a07a0aa4fdbad5ccd3c281/daily?marketplace_ids=tensor&start_date={today}"
    response = requests.get(url, headers=headers)
    response_json = response.json()
    pricelamp = response_json["floor_prices"][0]["floor_price"]
    price = pricelamp / 1000000000
    return price

def y00t_price():
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    today = datetime.date.today().isoformat()
    url = f"https://api.simplehash.com/api/v0/nfts/floor_prices_v2/collection/fddd6ff6f9e150f719b964d5f74e0734/daily?marketplace_ids=tensor&start_date={today}"
    response = requests.get(url, headers=headers)
    response_json = response.json()
    pricelamp = response_json["floor_prices"][0]["floor_price"]
    price = pricelamp / 1000000000
    return price

def gen3_price():
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    today = datetime.date.today().isoformat()
    url = f"https://api.simplehash.com/api/v0/nfts/floor_prices_v2/collection/63615c86e27c4ea1cf34c651d8442d9f/daily?marketplace_ids=tensor&start_date={today}"
    response = requests.get(url, headers=headers)
    response_json = response.json()
    pricelamp = response_json["floor_prices"][0]["floor_price"]
    price = pricelamp / 1000000000
    return price



@tasks.loop(seconds=14400)
async def pricehour():
    dustpriceall = dustprice()
    degod_prices = degod_price()
    y00t_prices = y00t_price()
    gen3_prices = gen3_price()

    channel = client.get_channel(1080342658901364777)
    
    await channel.send(content='Dust: ' + str(dustpriceall["priceUSD"]) +
                     " - Degods:  "   + str(degod_prices) + 
                     " - Y00ts:  "   + str(y00t_prices) + 
                     " - Gen3:  "  + str(gen3_prices))
    
client.run(Token)