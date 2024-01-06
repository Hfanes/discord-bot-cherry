import discord
from discord.ext import commands, tasks
import os
import requests
import locale
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from dotenv import load_dotenv

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
client = commands.Bot(command_prefix="$", intents=discord.Intents.all())
stop = False
previous_price = None
load_dotenv()
Token = os.getenv('OL')




previous_price_solana = None
previous_price_eth = None
previous_price_btc = None
previous_price_rune = None
previous_price_doge = None
previous_price_ada = None
previous_price_jup = None


channel__sol_id = int(os.getenv('SOL'))
channel_eth_id = int(os.getenv("ETH") )
channel_btc_id = int(os.getenv("BTC"))
channel_rune_id =int(os.getenv("RUNE"))
channel_doge_id =int(os.getenv("DOGE"))
channel_ada_id = int(os.getenv("ADA"))
channel_jup_id = int(os.getenv("JUP"))
cmc_api_key =    os.getenv('CMC_API_KEY')



@client.event
async def on_ready():
  print("Logged in as {0.user}".format(client))
  pricehour.start()
  change_channel_name_loop.start()


@tasks.loop(seconds=600)
async def change_channel_name_loop():
  await channel_name_solana()
  await channel_name_eth()
  await channel_name_btc()
  await channel_name_rune()
  await channel_name_doge()
  await channel_name_ada()
  await channel_name_jup()


async def channel_name_solana():
  global previous_price_solana
  channel = client.get_channel(channel__sol_id)

  if channel:
    try:
      current_price = solanaPriceCMC()
      emoji = ""  # Default emoji for equal prices
      if previous_price_solana is not None:
        if current_price > previous_price_solana:
          emoji = "🟢"
        elif current_price < previous_price_solana:
          emoji = "🔴"

      new_channel_name = f"{emoji}SOL: ${current_price}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_solana = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


async def channel_name_eth():
  global previous_price_eth
  channel = client.get_channel(channel_eth_id)

  if channel:
    try:
      current_price = ethPriceCMC()
      emoji = ""  # Default emoji for equal prices
      if previous_price_eth is not None:
        if current_price > previous_price_eth:
          emoji = "🟢"
        elif current_price < previous_price_eth:
          emoji = "🔴"

      new_channel_name = f"{emoji}ETH: ${current_price}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_eth = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


async def channel_name_btc():
  global previous_price_btc
  channel = client.get_channel(channel_btc_id)

  if channel:
    try:
      current_price = btcPriceCMC()
      emoji = ""  # Default emoji for equal prices
      if previous_price_btc is not None:
        if current_price > previous_price_btc:
          emoji = "🟢"
        elif current_price < previous_price_btc:
          emoji = "🔴"

      new_channel_name = f"{emoji}BTC: ${current_price}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_btc = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


async def channel_name_rune():
  global previous_price_rune
  channel = client.get_channel(channel_rune_id)

  if channel:
    try:
      current_price = runePrice()
      emoji = ""  # Default emoji for equal prices
      if previous_price_rune is not None:
        if current_price > previous_price_rune:
          emoji = "🟢"
        elif current_price < previous_price_rune:
          emoji = "🔴"

      new_channel_name = f"{emoji}RUNE: ${current_price}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_rune = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


async def channel_name_doge():
  global previous_price_doge
  channel = client.get_channel(channel_doge_id)

  if channel:
    try:
      current_price = float(dogePrice())
      emoji = ""  # Default emoji for equal prices
      if previous_price_doge is not None:
        if current_price > previous_price_doge:
          emoji = "🟢"
        elif current_price < previous_price_doge:
          emoji = "🔴"

      new_channel_name = f"{emoji}DOGE: ${current_price:.2f}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_doge = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


async def channel_name_ada():
  global previous_price_ada
  channel = client.get_channel(channel_ada_id)

  if channel:
    try:
      current_price = adaPrice()
      emoji = "💩"  # Default emoji for equal prices
      if previous_price_ada is not None:
        if current_price > previous_price_ada:
          emoji = "💩🟢"
        elif current_price < previous_price_ada:
          emoji = "💩🔴"

      new_channel_name = f"{emoji}ADA: ${current_price}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_ada = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


async def channel_name_jup():
  global previous_price_jup
  channel = client.get_channel(channel_jup_id)

  if channel:
    try:
      current_price = float(jupPrice())
      emoji = ""  # Default emoji for equal prices
      if previous_price_jup is not None:
        if current_price > previous_price_jup:
          emoji = "🟢"
        elif current_price < previous_price_jup:
          emoji = "🔴"

      new_channel_name = f"{emoji}JUP: ${current_price:.2f}"

      if isinstance(channel, discord.VoiceChannel):
        await channel.edit(name=new_channel_name)
        print(f"Nome do canal de voz alterado para: {new_channel_name}")
      else:
        print("Canal não é um canal de voz.")
      previous_price_jup = current_price
    except Exception as e:
      print(f"Erro ao obter dados do preço: {e}")
  else:
    print("Canal não encontrado.")


def solanaPriceCMC():
  url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
  parameters = {'id': 5426}
  headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': cmc_api_key,
  }

  session = Session()
  session.headers.update(headers)

  try:
    response = session.get(url, params=parameters)
    response_json = response.json()
    solana_price = response_json['data']['5426']['quote']['USD']['price']
    formatted_solana_price = "{:.2f}".format(solana_price)
    print(formatted_solana_price)
  except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)
  return formatted_solana_price


def ethPriceCMC():
  url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
  parameters = {'id': 1027}
  headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': cmc_api_key,
  }

  session = Session()
  session.headers.update(headers)

  try:
    response = session.get(url, params=parameters)
    response_json = response.json()
    eth_price = response_json['data']['1027']['quote']['USD']['price']
    formatted_eth_price = "{:.2f}".format(eth_price)
    print(formatted_eth_price)
  except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)
  return formatted_eth_price


def btcPriceCMC():
  url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
  parameters = {'id': 1}
  headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': cmc_api_key,
  }

  session = Session()
  session.headers.update(headers)

  try:
    response = session.get(url, params=parameters)
    response_json = response.json()
    btc_price = response_json['data']['1']['quote']['USD']['price']
    formatted_btc_price = "{:.2f}".format(btc_price)
    print(formatted_btc_price)
  except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)
  return formatted_btc_price


def runePrice():
  response = requests.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=thorchain&vs_currencies=usd"
  )
  response_json = response.json()

  runereturn = response_json["thorchain"]["usd"]
  return runereturn


def dogePrice():
  response = requests.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=dogecoin&vs_currencies=usd"
  )
  response_json = response.json()

  dogereturn = response_json["dogecoin"]["usd"]
  return dogereturn


def adaPrice():
  response = requests.get(
      "https://api.coingecko.com/api/v3/simple/price?ids=cardano&vs_currencies=usd"
  )
  response_json = response.json()

  adareturn = response_json["cardano"]["usd"]
  return adareturn


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
  print("Aqui")
  await channel.send(content='Dust: ' + str(dustpriceall["priceUSD"]) +
                     " - Degods: Ξ" + str(degodspricesall["floorPriceETH"]) +
                     " - Y00ts: Ξ" + str(y00tspriceall["floorPriceETH"]),
                     embed=embed)


client.run(Token)