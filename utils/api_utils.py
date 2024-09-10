import datetime
import aiohttp
import os

import requests
from config.settings import CMC_API_KEY,SIMPLE_API_KEY


headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': CMC_API_KEY,
}
simple_api_key = SIMPLE_API_KEY


async def get_crypto_price(id):
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    parameters = {'id': id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=parameters) as response:
                response_json = await response.json()
                crypto_price = response_json['data'][str(id)]['quote']['USD']['price']
                formatted_crypto_price = "{:.2f}".format(crypto_price)
                return formatted_crypto_price
    except aiohttp.ClientError as e:
        print(e)
        return None

async def get_coingecko_crypto_price(symbol):
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
    
async def fetch_coingecko_ids():
    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json() 
                return [item['id'] for item in data]
    except aiohttp.ClientError as e:
        print(f"HTTP error: {e}")
        return []

async def fetch_nft_collections():
    nfturl = "https://api.simplehash.com/api/v0/nfts/collections/top_v2?chains=solana&time_period=24h&limit=100"
    headers = {
        "accept": "application/json",
        "X-API-KEY": simple_api_key,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nfturl, headers=headers) as response:
                data = await response.json()  # Ensure to await the JSON decoding
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
    
async def command_nft_price(nftid, simple_api_key):
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
