# bot.py
import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from commands import setup_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is online and ready!')
    print(f'Connected to {len(bot.guilds)} servers')
    # Register commands
    setup_commands(bot)

# Error handling
def setup_error_handlers(bot):
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send('❌ Command not found! Use `!help_rl` to see available commands.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'❌ Missing required argument. Use `!help_rl` for command usage.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f'❌ Invalid argument provided. Use `!help_rl` for correct usage.')
        else:
            print(f'Error in command {ctx.command}: {error}')
            await ctx.send(f'❌ An error occurred. Please try again or contact support.')

setup_error_handlers(bot)

if __name__ == '__main__':
    print('Starting RL Stats Bot with RapidAPI...')
    print('Note: Get your RapidAPI key from rapidapi.com!')
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable not set!")
    bot.run(DISCORD_TOKEN)