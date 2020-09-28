import discord
import os
from discord.ext import commands

bot = commands.Bot(command_prefix=os.getenv('PREFIX'))


@bot.event
async def on_ready():
    print(f'{bot.user} logged in')

bot.run(os.getenv('DJ_TOKEN'))
