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


async def plotFunction(crypto, time_frame=30):
    data = await fetch_chart(crypto, time_frame)
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
    logo, name = await get_logo(crypto)
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
    logo, crypto_symbol = await get_logo(crypto)
    price, change1h, change24h, change7d, change30d, market_cap = await get_crypto_price(crypto)
    embed = discord.Embed(title=" ")
    embed.set_author(name=crypto_symbol + " - " + str(time_frame) + " Dias", url=logo, icon_url=logo)
    embed.add_field(name="🚀Price", value="$"+price, inline=True)
    embed.add_field(name="📅Change in 1h", value=change1h+"%", inline=True)
    embed.add_field(name="Change in 24h", value=change24h+"%", inline=True)
    embed.add_field(name="📅Change in 7d", value=change7d+"%", inline=True)
    embed.add_field(name="📅Change in 30d", value=change30d+"%", inline=True)
    embed.add_field(name="⭐Market Cap", value=market_cap, inline=True)
    embed.set_footer(text="with love to cherry crew🍒")
    embed.color = 0xA90101
    # Attach the updated chart image
    file = discord.File("./crypto_chart.png", filename='crypto_chart.png')
    embed.set_image(url='attachment://crypto_chart.png')
    return embed, file