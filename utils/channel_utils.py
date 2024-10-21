import discord
from utils.api_utils import fetch_chart, get_logo
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
from io import BytesIO
import requests
from utils.api_utils import get_crypto_price, fetch_chart, get_logo


async def update_channel(bot, channel_id, previous_price, crypto_price, emoji, symbol):
    """
    Update channel with new price
    """
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            if previous_price is not None:
                if crypto_price > previous_price:
                    emoji = "🟢↘️"
                elif crypto_price < previous_price:
                    emoji = "🔴↗️"

            new_channel_name = f"{emoji}{symbol}: ${crypto_price}"

            if isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=new_channel_name)
                print(f"Channel updated: {new_channel_name}")
            else:
                print("Not a voice channel.")
            previous_price = crypto_price
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Channel not found.")


async def plotFunction(crypto, data, time_frame=30):
    """
    Generates and saves a chart for the given crypto using provided price data.
    """
    values = data['prices']
    timestamps = [datetime.fromtimestamp(value[0] / 1000) for value in values]
    values_prices = [value[1] for value in values]
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='#252e33')
    ax.plot(timestamps, values_prices, label=crypto.capitalize(), color="#ff9904")
    ax.tick_params(axis='both', which='major', labelsize=6, color="#ffff")
    ax.grid(True, color='#121719', linestyle='-', linewidth=0.5)
    ax.set_facecolor('#252e33')
    ax.set_title(f'{crypto.capitalize()} Price Chart', color='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    logo = await get_logo(crypto)
    if logo:
        response = requests.get(logo)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        logo_width, logo_height = img.size
        fig_width, fig_height = fig.get_size_inches() * fig.dpi
        center_x = (fig_width - logo_width) / 2
        center_y = (fig_height - logo_height) / 2
        fig.figimage(img, xo=center_x, yo=center_y, alpha=0.4, zorder=1)

    plt.savefig('crypto_chart.png', facecolor='#252e33')
    plt.close()


async def embedFunction(crypto, time_frame):
    """
    Generates an embed with plot image and prices
    """
    logo, crypto_symbol = await get_logo(crypto)
    price, change1h, change24h, change7d, change30d, market_cap = await get_crypto_price(crypto)
    embed = discord.Embed(title=" ")
    embed.set_author(
    name=f"{crypto_symbol} - {str(time_frame)} days" if crypto_symbol is not None and time_frame is not None else "Unavailable",
    url=logo,
    icon_url=logo
    )
    embed.add_field(name="🚀Price", value=f"${price}" if price is not None else "Unavailable", inline=True)
    embed.add_field(name="📅Change in 1h", value=f"{change1h}%" if change1h is not None else "Unavailable", inline=True)
    embed.add_field(name="Change in 24h", value=f"{change24h}%" if change24h is not None else "Unavailable", inline=True)
    embed.add_field(name="📅Change in 7d", value=f"{change7d}%" if change7d is not None else "Unavailable", inline=True)
    embed.add_field(name="📅Change in 30d", value=f"{change30d}%" if change30d is not None else "Unavailable", inline=True)
    embed.add_field(name="⭐Market Cap", value=f"{market_cap}%" if market_cap is not None else "Unavailable", inline=True)
    embed.set_footer(text="with love to cherry crew🍒")
    embed.color = 0xA90101
    # Attach the updated chart image
    file = discord.File("./crypto_chart.png", filename='crypto_chart.png')
    embed.set_image(url='attachment://crypto_chart.png')
    return embed, file