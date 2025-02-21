import random
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='?', 
    intents=intents)

def dice_roll(dice: str):
    try:
        rolls, limit = map(int, dice.split('d'))
    except ValueError:
        return None
    
    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    return result

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command(name='roll')
async def roll(ctx, dice: str):
    result = dice_roll(dice=dice)

    if result is None:
        await ctx.send('⚠️ Format has to be NdN, ex: 1d4. ⚠️')
        return

    await ctx.send(result)

bot.run(token)