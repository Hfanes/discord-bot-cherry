import discord
from discord.ext import commands, tasks
import os
import requests
import locale
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from dotenv import load_dotenv
import asyncio

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
client = commands.Bot(command_prefix="$", intents=discord.Intents.all())
stop = False
previous_price = None
previous_price_jup = None
load_dotenv()
Token = os.getenv('OL')



cryptosCMC = {
    'solana': {'id': 5426, 'channel_id': int(os.getenv('SOL')), 'previous_price': None},
    'ethereum': {'id': 1027, 'channel_id': int(os.getenv('ETH')), 'previous_price': None},
    'bitcoin': {'id': 1, 'channel_id': int(os.getenv('BTC')), 'previous_price': None},
}

cryptosCG = {
    'rune': {'symbol': 'thorchain','channel_id': int(os.getenv('RUNE')), 'previous_price': None},
    'doge': {'symbol': 'dogecoin','channel_id': int(os.getenv('DOGE')), 'previous_price': None},
    'ada': { 'symbol': 'cardano','channel_id': int(os.getenv('ADA')), 'previous_price': None},
}

cmc_api_key = os.getenv('CMC_API_KEY')



@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    change_channel_name_loop.start()
    await asyncio.sleep(61)
    pricehour.start()



@tasks.loop(seconds=810)
async def change_channel_name_loop():
    global previous_price_jup  # Declare as global
    for crypto, info in cryptosCMC.items():
        current_price = get_crypto_price(info['id'])
        await update_channel(info['channel_id'], info['previous_price'], current_price, "", crypto.upper())
        info['previous_price'] = current_price

    for crypto, info in cryptosCG.items():
        current_price = get_coingecko_crypto_price(info['symbol'])
        await update_channel(info['channel_id'], info['previous_price'], current_price, "", crypto.upper())
        info['previous_price'] = current_price
        await asyncio.sleep(5)

    current_price_jup = jupPrice()
    await update_channel(int(os.getenv('JUP')), previous_price_jup, current_price_jup, "", 'JUP')
    previous_price_jup = current_price_jup

    


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
            print(f"Key error: {symbol} or 'usd' not found in response.")
            return None
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        return None



def jupPrice():
  url = "https://api.aevo.xyz/markets?asset=JUP"

  headers = {"accept": "application/json"}

  response = requests.get(url, headers=headers)
  response_json = response.json()
  jup_price = response_json[0]['mark_price']
  return jup_price


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


def degodsprice():
  response = requests.get("https://api.coingecko.com/api/v3/nfts/degods")
  response_json = response.json()

  degods_pricesreturn = {
      "floorPriceETH":
      response_json["floor_price"]["native_currency"],
      "floorPriceUSD":
      locale.currency(response_json["floor_price"]["usd"], grouping=True),
      "h24change":
      response_json["floor_price_in_usd_24h_percentage_change"]
  }
  return degods_pricesreturn


def y00tsprice():
  response = requests.get("https://api.coingecko.com/api/v3/nfts/y00ts")
  response_json = response.json()

  y00ts_pricesreturn = {
      "floorPriceETH":
      response_json["floor_price"]["native_currency"],
      "floorPriceUSD":
      locale.currency(response_json["floor_price"]["usd"], grouping=True),
      "h24change":
      response_json["floor_price_in_usd_24h_percentage_change"]
  }
  return y00ts_pricesreturn


@tasks.loop(seconds=14400)
async def pricehour():
  degodspricesall = degodsprice()
  y00tspriceall = y00tsprice()
  dustpriceall = dustprice()
  channel = client.get_channel(1080342658901364777)
  embed = discord.Embed(title="De Alert", color=0x4089e7)
  embed.set_thumbnail(
      url=
      "https://assets.coingecko.com/nft_contracts/images/3145/small/degods.png?1680194340"
  )
  embed.add_field(name="Dust:",
                  value=str(dustpriceall["priceUSD"]),
                  inline=True)
  embed.add_field(name="|", value="|", inline=True)
  embed.add_field(name="24h Change: ",
                  value=str(dustpriceall["h24change"]) + "%",
                  inline=True)
  embed.add_field(name="Degods: ",
                  value="Ξ " + str(degodspricesall["floorPriceETH"]) + "\t" +
                  str(degodspricesall["floorPriceUSD"]),
                  inline=True)
  embed.add_field(name="|", value="|", inline=True)
  embed.add_field(name=" 24h Change:",
                  value=str(degodspricesall["h24change"]) + "%",
                  inline=True)
  embed.add_field(name="Y00ts: ",
                  value="Ξ " + str(y00tspriceall["floorPriceETH"]) + "\t" +
                  str(y00tspriceall["floorPriceUSD"]),
                  inline=True)
  embed.add_field(name="|", value="|", inline=True)
  embed.add_field(name=" 24h Change:",
                  value=str(y00tspriceall["h24change"]) + "%",
                  inline=True)
  print("Delabs Prices")
  await channel.send(content='Dust: ' + str(dustpriceall["priceUSD"]) +
                     " - Degods: Ξ" + str(degodspricesall["floorPriceETH"]) +
                     " - Y00ts: Ξ" + str(y00tspriceall["floorPriceETH"]),
                     embed=embed)


client.run(Token)