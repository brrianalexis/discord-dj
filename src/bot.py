import discord
import os
from discord.ext import commands

bot = commands.Bot(command_prefix=os.getenv('PREFIX'))

# pipenv run lavalink para levantar el servidor de lavalink
# pipenv run dev para levantar el bot


@bot.event
async def on_ready():
    print(f'{bot.user} logged in')
    bot.load_extension('cogs.dj')

bot.run(os.getenv('DJ_TOKEN'))
