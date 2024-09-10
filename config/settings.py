import os
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv('CMC_API_KEY')
SIMPLE_API_KEY = os.getenv('simple_api_key')

SOL_CHANNEL_ID = int(os.getenv('SOL'))
ETH_CHANNEL_ID = int(os.getenv('ETH'))
BTC_CHANNEL_ID = int(os.getenv('BTC'))
RUNE_CHANNEL_ID = int(os.getenv('RUNE'))
DOGE_CHANNEL_ID = int(os.getenv('DOGE'))
W_CHANNEL_ID = int(os.getenv('W'))
WIF_CHANNEL_ID = int(os.getenv('WIF'))
JUP_CHANNEL_ID = int(os.getenv('JUP'))

TOKEN = os.getenv('OL')