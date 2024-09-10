import discord

async def update_channel(bot, channel_id, previous_price, crypto_price, emoji, symbol):
    channel = bot.get_channel(channel_id)
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