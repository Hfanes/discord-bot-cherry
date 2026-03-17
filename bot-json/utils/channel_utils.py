from decimal import Decimal
import discord
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
from io import BytesIO
import requests

async def update_channel(bot, channel_id, previous_price, crypto_price, symbol_display):
    print("update_channel")
    """
    Update channel with new price
    """
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            emoji = ""
            if previous_price is not None:
                previous_price = Decimal(previous_price)
                crypto_price = Decimal(crypto_price)
                if crypto_price > previous_price:
                    emoji = "🟢↗️"
                elif crypto_price < previous_price:
                    emoji = "🔴↘️"
                else: 
                    emoji

            new_channel_name = f"{emoji}{symbol_display.upper()}: ${crypto_price}"

            if isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=new_channel_name)
                print(f"Channel updated: {new_channel_name}")
                return new_channel_name
            else:
                print("Not a voice channel.")
                return 
        
        except Exception as e:
            print(f"Error updating channel {channel_id}: {e}")
    else:
        print("Channel not found.")
        return None


async def plotFunction(crypto, data, logo):
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


async def embedFunction(time_frame, name, logo, market_cap, price, high_24h, low_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d):
    """
    Generates an embed with plot image and prices
    """
    embed = discord.Embed(title="⭐ Market Cap: " + str(market_cap))
    embed.set_author(
    name=f"{name} - {str(time_frame)} days" if name is not None and time_frame is not None else "Unavailable",
    url=logo,
    icon_url=logo
    )
    embed.add_field(name="🚀 Price", value=f"${price}" if price is not None else "Unavailable", inline=True)
    embed.add_field(name="↗️ Highest in 24h", value=f"${high_24h}" if high_24h is not None else "Unavailable", inline=True)
    embed.add_field(name="↘️ Lowest in 24h", value=f"${low_24h}" if low_24h is not None else "Unavailable", inline=True)
    embed.add_field(name="📅 Change in 24h", value=f"{price_change_percentage_24h}%" if price_change_percentage_24h is not None else "Unavailable", inline=True)
    embed.add_field(name="📅 Change in 7d", value=f"{price_change_percentage_7d}%" if price_change_percentage_7d is not None else "Unavailable", inline=True)
    embed.add_field(name="📅 Change in 30d", value=f"{price_change_percentage_30d}%" if price_change_percentage_30d is not None else "Unavailable", inline=True)
    embed.set_footer(text="with love to cherry crew 🍒")
    embed.color = 0xA90101
    # Attach chart image
    file = discord.File("./crypto_chart.png", filename='crypto_chart.png')
    embed.set_image(url='attachment://crypto_chart.png')
    return embed, file