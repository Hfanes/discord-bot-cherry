import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.api_utils import command_coin_price, command_nft_price, fetch_coingecko_ids, fetch_nft_collections, get_coingecko_crypto_price, get_crypto_price, fetch_chart
from utils.channel_utils import plotFunction, embedFunction, update_channel
from utils.database import create_connection, create_tables
import asyncio
from discord import app_commands
import typing


load_dotenv()
TOKEN = os.getenv('OL')
coins_100_ids = []
collections_nft = {}
intents = discord.Intents.all()
intents.guilds = True 
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    await bot.tree.sync()
    await setup_data()
    await create_tables()
    change_channel_name_loop.start()


async def setup_data():
    global coins_100_ids, collections_nft
    coins_100_ids = await fetch_coingecko_ids()
    collections_nft = await fetch_nft_collections()


@bot.tree.command(description="Create VC price", name="create")
async def create(interaction: discord.Interaction, crypto: str):
    guild = interaction.guild
    try:
        if crypto.lower() in ["solana", "bitcoin", "ethereum"]:
            price, symbol_display = await get_crypto_price(crypto)
        else:
            price, symbol_display = await get_coingecko_crypto_price(crypto)

        if price is None:
            await interaction.response.send_message(f"Symbol '{crypto}' is invalid or not supported.")
            return

        voice_channel = await guild.create_voice_channel(crypto)

        server_id = int(guild.id)
        channel_id = int(voice_channel.id)

        #server and channel information into the database
        await insert_server_channel(server_id, channel_id, crypto, guild.name, price)
        # Set the channel name with the price
        await voice_channel.edit(name=f"{symbol_display.upper()}: ${price}")
        await interaction.response.send_message(f"Voice channel created for {crypto}!")

    except discord.Forbidden:
        await interaction.response.send_message("Cherry bot doesn't have 'Manage Channels' permissions.")
        print(f"Permission denied: Unable to create voice channel for {crypto}.")
    except Exception as e:
        print(f"Error: {e}")
        await interaction.response.send_message("Failed to create voice channel")

@create.autocomplete("crypto")
async def coin_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_ids = []
    for id_choice in coins_100_ids:
     if current.lower() in id_choice.lower():
        filtered_ids.append(id_choice)
    choices = [
        app_commands.Choice[str](name=id_choice, value=id_choice) 
        for id_choice in filtered_ids[:25]
    ]
    return choices

#SELECT * FROM users WHERE id = 12345; DROP TABLE servers; -- 
#vs
#SELECT * FROM users WHERE id = '12345; DROP TABLE servers; --'
async def insert_server_channel(server_id, channel_id, crypto_id, server_name, initial_price):
    conn = await create_connection()
    try:
        # Insert the server info, avoiding duplicates
        insert_server_query = """
            INSERT INTO servers (discord_id, name) 
            VALUES ($1, $2)
            ON CONFLICT (discord_id) DO NOTHING;
        """
        await conn.execute(insert_server_query, server_id, server_name)

        insert_channel_query = """
            INSERT INTO channels (server_id, channel_id, crypto_id, previous_price) 
            VALUES ($1, $2, $3, $4)
        """
        await conn.execute(insert_channel_query, server_id, channel_id, crypto_id, initial_price)
        print(f"Voice channel created for {crypto_id}!")

    except Exception as e:
        print(f"Error inserting {crypto_id} in {server_id}: {e}")
        await conn.close()
    finally:
        print("con closed")
        await conn.close()

    
@tasks.loop(seconds=900)
async def change_channel_name_loop():
    # Connect to the database from database.py connection
    conn = await create_connection()
    try:
        # Retrieve all channels for all servers
        channels = await conn.fetch("""
            SELECT c.channel_id, c.crypto_id, c.previous_price, s.discord_id, s.name
            FROM channels c
            INNER JOIN servers s ON c.server_id = s.discord_id
        """)

        if not channels:
            print("No channels found in the database")
            return
        
        for row in channels:
            channel_id = int(row['channel_id'])
            crypto_id = row['crypto_id']
            previous_price = row['previous_price']
            server_name = row['name']
            discord_id = int(row['discord_id'])

            if crypto_id.lower() in ["solana", "bitcoin", "ethereum"]:
                current_price, symbol_display = await get_crypto_price(crypto_id)
            else: 
                current_price, symbol_display = await get_coingecko_crypto_price(crypto_id)
            
            if current_price is not None:
                name_updated = await update_channel(bot, channel_id, previous_price, current_price, symbol_display)
                if name_updated is None:
                    print(f"Channel {channel_id} not found in Discord; verifying permissions.")
                    # Check if bot has permission to manage channels in this guild
                    guild = bot.get_guild(discord_id)
                    if guild and guild.me.guild_permissions.manage_channels:
                        delete_query = "DELETE FROM channels WHERE channel_id = $1"
                        await conn.execute(delete_query, channel_id)
                        print(f"Deleted channel {channel_id} from database as it no longer exists on Discord {server_name}.")
                    else:
                        print(f"Insufficient permissions to delete channel {channel_id} from database.")
                    continue
                print(f"Channel from {server_name} updated to {name_updated}")
                await asyncio.sleep(10)
            else:
                print(f"Error changing {server_name} channel {channel_id}")
                continue
                
            #update previous_price    
            update_query = "UPDATE channels SET previous_price = $1 WHERE channel_id = $2"
            await conn.execute(update_query, current_price, channel_id)

    except Exception as e:
        print(f"Error updating channel names: {e}")
        await conn.close()
    finally:
        await conn.close()

@bot.tree.command(name='sync', description='Sync')
async def sync(interaction: discord.Interaction):
    await bot.tree.sync()
    print('Command tree synced.')

@bot.tree.command(name='help', description='Show help with all commands')
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="🍒 Cherry Help", description=(
            "Commands\n"
            "</chart:1299779930329972860> [crypto] Get coin chart price.\n"
            "Example: /chart bitcoin\n"
            "</nft:1240005817139466271> [NFT-Collection-name] Solana Nft collection floor price.\n"
            "Example: /nft claynosaurz\n"
            "</price:1298068375724883969> [crypto] Get coin price in usd.\n"
            "Example: /price bitcoin\n"
            "</create:1299779930329972857> [crypto] Create a voice channel with crypto price.\n"
            "Example: /create bitcoin\n"
            "\n Useful information \n"
            "Crypto-ID ➡️ Visit [coingecko.com](https://coingecko.com), search for any crypto you want to add, copy the API ID"
        ))
    embed.color = 0xA90101
    await interaction.response.send_message(embed=embed)


@bot.tree.command(description="Coin price chart", name="chart")
async def chart(interaction: discord.Interaction, crypto: str):
    crypto = crypto.lower()
    time_frame=30
    try:
        data = await fetch_chart(crypto, time_frame)
        name, logo, market_cap, price, high_24h, low_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d = await command_coin_price(crypto)
        if not data:
            await interaction.response.send_message(f"Error with {crypto}. Please try again later. Or verify coin ID")
            return
        await plotFunction(crypto, data, logo)
        _embed, _file = await embedFunction(time_frame, name, logo, market_cap, price, high_24h, low_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d)
        await interaction.response.send_message(embed=_embed,file=_file, view = MyView(crypto))
    except Exception:
        await interaction.response.send_message(f"You need the API ID - https://www.coingecko.com/")
    
@chart.autocomplete("crypto")
async def coin_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_ids = []
    for id_choice in coins_100_ids:
     if current.lower() in id_choice.lower():
        filtered_ids.append(id_choice)
    choices = [
        app_commands.Choice[str](name=id_choice, value=id_choice) 
        for id_choice in filtered_ids[:25]
    ]
    return choices


class MyView(discord.ui.View):
    def __init__(self, crypto):
        super().__init__(timeout=None)
        self.crypto = crypto
    @discord.ui.button(label="Reload", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def reload_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.reload_chart(interaction, self.crypto)

    @discord.ui.button(label="7d", style=discord.ButtonStyle.secondary, emoji="📅")
    async def reload__7d_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.reload_chart(interaction, self.crypto, time_frame=7)

    @discord.ui.button(label="30d", style=discord.ButtonStyle.secondary, emoji="📅")
    async def reload_30d_button_callback(self, interaction: discord.Interaction, button: discord.ui.button):
        await self.reload_chart(interaction, self.crypto, time_frame=30)

    #reload
    async def reload_chart(self, interaction: discord.Interaction, crypto, time_frame=30):
        #More than 3 seconds
        await interaction.response.defer()
        try:
            data = await fetch_chart(crypto, time_frame)
            name, logo, market_cap, price, high_24h, low_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d = await command_coin_price(crypto)
            if not data:
                await interaction.followup.send(f"Error with {crypto}. Please try again later.")
                return
            await plotFunction(crypto, data, logo)
            _embed, _file = await embedFunction(time_frame, name, logo, market_cap, price, high_24h, low_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d)
            await interaction.edit_original_response(embed=_embed, attachments=[_file], view=self)
        except Exception as e:
            await interaction.followup.send(f"Error while reloading data for {crypto}. Please try again later.")
            print(f"Error reloading chart for {crypto}: {e}")
        
        
@bot.tree.command(description="Coin price", name="price")
async def price(interaction: discord.Interaction, symbol: str):
    symbol = symbol.lower()
    try:
        value = await get_coingecko_crypto_price(symbol)
        if not value :
            await interaction.response.send_message(f"Error with {symbol}. Please try again later. Or verify coin ID")
            return
        await interaction.response.send_message(f"Price off {symbol}: {value}$")
    except Exception:
        await interaction.response.send_message(f"You need the API ID - https://www.coingecko.com/")
        return

@price.autocomplete("symbol")
async def coin_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_ids = []
    for id_choice in coins_100_ids:
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
    for id_, name in collections_nft.items():
        if name.lower() == nft:
            nft_id = id_
            break
    if nft_id:
        value = await command_nft_price(nft_id)
        if not value :
            await interaction.response.send_message(f"Error with {nft}. Please try again later. Or verify nft collection name")
            return
        await interaction.response.send_message(f"{nft} floor price: {value} SOL")
    
@nft.autocomplete("nft")
async def nft_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> typing.List[app_commands.Choice[str]]:
    filtered_nft = []
    for nft_id, nft_name in collections_nft.items():
     if current.lower() in nft_name.lower():
        filtered_nft.append(nft_name)
    choicesnft = [
        app_commands.Choice[str](name=nft_name, value=nft_name) 
        for nft_name in filtered_nft[:25]
    ]
    return choicesnft

bot.run(TOKEN)