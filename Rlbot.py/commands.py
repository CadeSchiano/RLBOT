import discord
from discord.ext import commands
import requests
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

def setup_commands(bot):
    @bot.command()
    async def hello(ctx):
        await ctx.send('🚗💨 RL Stats Bot is online! Using RapidAPI Rocket League API!')

    @bot.command()
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f'🏓 Pong! Bot latency: {latency}ms')

    @bot.command()
    async def test_api(ctx):
        await ctx.send('🔍 Testing RapidAPI Rocket League connection...')
        
        url = f"https://{RAPIDAPI_HOST}/ping"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                await ctx.send(f'✅ API working! Connection successful.')
            elif response.status_code == 401:
                await ctx.send('❌ API key invalid. Check your RapidAPI key.')
            elif response.status_code == 429:
                await ctx.send('⏳ API rate limit hit. Try again later.')
            else:
                await ctx.send(f'❌ API error. Status code: {response.status_code}')
        except requests.exceptions.Timeout:
            await ctx.send('⏰ API request timed out. Try again.')
        except Exception as e:
            await ctx.send(f'❌ Error testing API: {str(e)}')

    @bot.command()
    async def player_stats(ctx, platform='', player_id=''):
        if not platform or not player_id:
            await ctx.send('❌ Please provide platform and player ID!\n**Example:** `!player_stats epic Forky`\n**Platforms:** epic, steam, ps4, xboxone')
            return

        platform = platform.lower()
        await ctx.send(f'🔍 Fetching stats for {player_id} on {platform}...')
        
        url = f"https://{RAPIDAPI_HOST}/player/{platform}/{player_id}"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract player info
                player_name = data.get('displayName', player_id)
                platform_name = data.get('platform', {}).get('name', platform)
                
                # Create embed
                stats_embed = discord.Embed(
                    title=f"🚗 {player_name}'s Rocket League Stats",
                    description=f"Platform: {platform_name}",
                    color=0x00ff88
                )
                
                # Get stats if available
                stats = data.get('stats', {})
                if stats:
                    stats_embed.add_field(
                        name="📊 Career Stats",
                        value=f"**Wins:** {stats.get('wins', 'N/A')}\n**Goals:** {stats.get('goals', 'N/A')}\n**MVPs:** {stats.get('mvps', 'N/A')}\n**Saves:** {stats.get('saves', 'N/A')}\n**Assists:** {stats.get('assists', 'N/A')}\n**Shots:** {stats.get('shots', 'N/A')}",
                        inline=True
                    )
                
                # Get rank info if available
                playlists = data.get('playlists', {})
                if playlists:
                    rank_text = ""
                    for playlist_name, playlist_data in playlists.items():
                        if isinstance(playlist_data, dict) and playlist_data.get('tier'):
                            tier = playlist_data.get('tier', 'Unranked')
                            division = playlist_data.get('division', 0)
                            mmr = playlist_data.get('skillRating', 'N/A')
                            rank_text += f"**{playlist_name}:** {tier} Div {division} ({mmr} MMR)\n"
                    
                    if rank_text:
                        stats_embed.add_field(
                            name="🏆 Ranked Playlists",
                            value=rank_text,
                            inline=False
                        )
                
                stats_embed.set_footer(text=f"Player ID: {player_id}")
                await ctx.send(embed=stats_embed)
                
            elif response.status_code == 404:
                await ctx.send(f'❌ Player **{player_id}** not found on {platform}.\n💡 Make sure the username and platform are correct!')
            else:
                await ctx.send(f'❌ Error fetching data. Status code: {response.status_code}')
                
        except Exception as e:
            await ctx.send(f'❌ Error: {str(e)}')

    @bot.command()
    async def player_rank(ctx, platform='', player_id=''):
        if not platform or not player_id:
            await ctx.send('❌ Please provide platform and player ID!\n**Example:** `!player_rank epic Forky`')
            return

        platform = platform.lower()
        await ctx.send(f'🔍 Fetching ranks for {player_id}...')
        
        url = f"https://{RAPIDAPI_HOST}/player/{platform}/{player_id}"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                player_name = data.get('displayName', player_id)
                
                embed = discord.Embed(
                    title=f"🏆 {player_name}'s Ranks",
                    color=0x0099ff
                )
                
                playlists = data.get('playlists', {})
                if playlists:
                    for playlist_name, playlist_data in playlists.items():
                        if isinstance(playlist_data, dict) and playlist_data.get('tier'):
                            tier = playlist_data.get('tier', 'Unranked')
                            division = playlist_data.get('division', 0)
                            mmr = playlist_data.get('skillRating', 'N/A')
                            wins = playlist_data.get('wins', 0)
                            matches = playlist_data.get('matchesPlayed', 0)
                            
                            value_text = f"**Rank:** {tier} Div {division}\n**MMR:** {mmr}\n**Record:** {wins}W / {matches} Games"
                            embed.add_field(name=playlist_name, value=value_text, inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f'❌ No rank data found for {player_name}')
            else:
                await ctx.send(f'❌ Error fetching rank data. Status: {response.status_code}')
                
        except Exception as e:
            await ctx.send(f'❌ Error: {str(e)}')

    @bot.command()
    async def find_player(ctx, *, search_term=''):
        if not search_term:
            embed = discord.Embed(
                title="🔍 How to Find Players",
                description="Learn how to look up player stats",
                color=0x5B2071
            )
            embed.add_field(
                name="Player ID Format",
                value="You need the player's **exact username** and **platform**",
                inline=False
            )
            embed.add_field(
                name="Supported Platforms",
                value="• **epic** - Epic Games\n• **steam** - Steam\n• **ps4** - PlayStation\n• **xboxone** - Xbox",
                inline=False
            )
            embed.add_field(
                name="Example Commands",
                value="`!player_stats epic Forky`\n`!player_rank steam Kronovi`\n`!player_stats ps4 YourUsername`",
                inline=False
            )
            embed.set_footer(text="💡 Usernames are case-sensitive!")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'💡 To look up **{search_term}**, use:\n`!player_stats [platform] {search_term}`\n\nPlatforms: epic, steam, ps4, xboxone')

    @bot.command()
    async def population(ctx):
        await ctx.send('🔍 Fetching current playlist populations...')
        
        url = f"https://{RAPIDAPI_HOST}/population"
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                embed = discord.Embed(
                    title="🎮 Current Playlist Populations",
                    description="Live player counts across all playlists",
                    color=0x00ff88
                )
                
                playlists = data.get('playlists', [])
                if playlists:
                    for playlist in playlists[:10]:  # Show top 10
                        name = playlist.get('name', 'Unknown')
                        count = playlist.get('population', 0)
                        embed.add_field(
                            name=name,
                            value=f"**{count:,}** players",
                            inline=True
                        )
                
                total = data.get('totalPlayers', 0)
                embed.set_footer(text=f"Total Online: {total:,} players")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f'❌ Error fetching population data. Status: {response.status_code}')
                
        except Exception as e:
            await ctx.send(f'❌ Error: {str(e)}')

    @bot.command(name='help_rl')
    async def help_rl(ctx):
        embed = discord.Embed(
            title="🚀 RL Stats Bot Commands",
            description="Powered by RapidAPI Rocket League API",
            color=0x00ff88
        )
        
        embed.add_field(
            name="🧪 Test Commands",
            value="`!hello` - Basic bot test\n`!ping` - Check latency\n`!test_api` - Test API connection",
            inline=False
        )
        embed.add_field(
            name="📊 Stats Commands",
            value="`!player_stats [platform] [username]` - Full player stats\n`!player_rank [platform] [username]` - Player ranks\n`!find_player [name]` - Help finding players",
            inline=False
        )
        embed.add_field(
            name="🎮 Info Commands",
            value="`!population` - Current playlist populations\n`!help_rl` - Show this help message",
            inline=False
        )
        embed.add_field(
            name="💡 Examples",
            value="`!player_stats epic Forky`\n`!player_rank steam Kronovi`\n`!population`",
            inline=False
        )
        embed.add_field(
            name="🌐 Platforms",
            value="**epic** | **steam** | **ps4** | **xboxone**",
            inline=False
        )
        embed.set_footer(text="Use !find_player for more help")
        await ctx.send(embed=embed)