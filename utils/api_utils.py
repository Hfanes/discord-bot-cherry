import datetime
import aiohttp
from config.settings import CMC_API_KEY,SIMPLE_API_KEY


headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': CMC_API_KEY,
}
simple_api_key = SIMPLE_API_KEY


async def get_crypto_price(crypto):
    """
    Get price of a coin (COINMARKETCAP)
    """
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    params = {'slug': crypto}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response_json = await response.json()
                for key in response_json["data"]:
                            price = response_json["data"][key]['quote']['USD']['price']
                            change1h = response_json["data"][key]['quote']['USD']['percent_change_1h']
                            change24h = response_json["data"][key]['quote']['USD']['percent_change_24h']
                            change7d = response_json["data"][key]['quote']['USD']['percent_change_7d']
                            change30d = response_json["data"][key]['quote']['USD']['percent_change_30d']
                            market_cap = response_json["data"][key]['quote']['USD']['market_cap']
                            #array of formatted_values
                            formatted_values = ["{:.2f}".format(value) for value in [price, change1h, change24h, change7d, change30d, market_cap]]
                            formatted_price, formatted_change1h, formatted_change24h, formatted_change7d, formatted_change30d, formatted_market_cap = formatted_values
                            return formatted_price, formatted_change1h, formatted_change24h, formatted_change7d, formatted_change30d, formatted_market_cap
    except aiohttp.ClientError as e:
        print(f"Error fetching crypto price: {e}")
        return [None] * 6  # Return a list of Nones for consistency
    except Exception as e:
        print(f"Unexpected error for {crypto}: {e}")
        return [None] * 6


async def get_coingecko_crypto_price(symbol):
    """
    Get price of a coin (COINGECKO)
    """
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
                    print(f"Error with symbol: {symbol}")
                    return None
    except aiohttp.ClientError as e:
        print(f"HTTP error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {symbol}: {e}")
        return None
    
async def fetch_coingecko_ids():
    """
    Get id coins from coingecko to use to autocomplete
    """
    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json() 
                return [item['id'] for item in data]
    except aiohttp.ClientError as e:
        print(f"HTTP error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error for: {e}")
        return []

async def fetch_nft_collections():
    """
    Get the top solana collections in the previous 24h
    """
    nfturl = "https://api.simplehash.com/api/v0/nfts/collections/top_v2?chains=solana&time_period=24h&limit=100"
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nfturl, headers=headers) as response:
                data = await response.json()
                collections_dict = {}
                for collection in data.get("collections", []):
                    collection_details = collection.get("collection_details", {})
                    if collection_details:
                        name = collection_details.get("name")
                        collection_id = collection_details.get("collection_id")
                        collections_dict[collection_id] = name
                return collections_dict
    except aiohttp.ClientError as e:
        print(f"HTTP error: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error for: {e}")
        return None
    
async def command_nft_price(nftid, simple_api_key):
    """
    Get price of a nft using command /nft colletion 
    """
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    today = datetime.date.today().isoformat()
    url = f"https://api.simplehash.com/api/v0/nfts/floor_prices_v2/collection/{nftid}/daily?marketplace_ids=tensor&start_date={today}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response_json = await response.json()
                pricelamp = response_json["floor_prices"][0]["floor_price"]
                price = pricelamp / 1000000000
                return price
    except aiohttp.ClientError as e:
        print(f"HTTP error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {nftid}: {e}")
        return None

async def fetch_chart(crypto, time_frame=30):
    """
    Get the historical chart data of a coin 
    """
    url = f'https://api.coingecko.com/api/v3/coins/{crypto}/market_chart'
    params = {'vs_currency': 'usd', 'days': time_frame}
    print(time_frame)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    response_json = await response.json()
                    return response_json
                else:
                    print(f"Error: Received status code {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"HTTP Error while fetching chart: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {crypto}: {e}")
        return None

async def command_coin_price(crypto):
    """
    Get price, change1h, change24h, change7d, change30d, market_cap, logo, name
    """
    url=f"https://api.coingecko.com/api/v3/coins/{crypto}"
    try: 
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    response_json = await response.json()
                    name = response_json["name"]
                    logo = response_json["image"]["small"]
                    price = response_json["market_data"]["current_price"]["usd"]
                    market_cap = response_json["market_data"]["market_cap"]["usd"]
                    high_24h = response_json["market_data"]["high_24h"]["usd"]
                    low_24h = response_json["market_data"]["low_24h"]["usd"]
                    price_change_percentage_24h = response_json["market_data"]["price_change_percentage_24h"]
                    price_change_percentage_7d = response_json["market_data"]["price_change_percentage_7d"]
                    price_change_percentage_30d = response_json["market_data"]["price_change_percentage_30d"]

                    if market_cap >= 1000000000:  # Billions
                        formatted_market_cap = f"{market_cap / 1000000000:.1f}B"
                    elif market_cap >= 1000000:  # Millions
                        formatted_market_cap = f"{market_cap / 1000000:.1f}M"
                    elif market_cap >= 1000:  # Thousands
                        formatted_market_cap = f"{int(market_cap / 1000)}K"
                    else:
                        formatted_market_cap = str(market_cap)  # Less than 1,000

                    formatted_price = "{:.3f}".format(price) if price > 1 else "{:.7f}".format(price)
                    formatted_high_24h = "{:.3f}".format(high_24h) if high_24h > 1 else "{:.7f}".format(high_24h)
                    formatted_low_24h = "{:.3f}".format(low_24h) if low_24h > 1 else "{:.7f}".format(low_24h)
                    formatted_price_change_percentage_24h = "{:.2f}".format(price_change_percentage_24h)
                    formatted_price_change_percentage_7d = "{:.2f}".format(price_change_percentage_7d)
                    formatted_price_change_percentage_30d = "{:.2f}".format(price_change_percentage_30d)

                    return name, logo, formatted_market_cap, formatted_price, formatted_high_24h, formatted_low_24h, formatted_price_change_percentage_24h, formatted_price_change_percentage_7d, formatted_price_change_percentage_30d
    except aiohttp.ClientError as e:
        print(f"HTTP Error: {e}")
        return [None] * 9
    except Exception as e:
        print(f"Unexpected error for {crypto}: {e}")
        return [None] * 9
