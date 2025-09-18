import discord
from discord.ext import commands
import requests
import json
import asyncio
from datetime import datetime

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration - Replace with your tokens
DISCORD_TOKEN = 'MTQwOTIzMDY4NTU3MDQ2OTg5MQ.Gy5q_C.WGuumk9ZwXoZVUc5oyRQjpFJytO9S2NmNQxg3w'
BALLCHASING_API_KEY = 'ofFQrG5uTHxTSZalhV0oKfpOmJD0EtQ8EBOQOfEG'  # Get from ballchasing.com

BALLCHASING_BASE_URL = 'https://ballchasing.com/api'


@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is online and ready!')
    print(f'Connected to {len(bot.guilds)} servers')

    # Test the API connection
    await test_api_connection()


async def test_api_connection():
    """Test if our Ballchasing API key works"""
    headers = {
        'Authorization': BALLCHASING_API_KEY
    }

    try:
        # Test API call - get recent replays
        response = requests.get(f'{BALLCHASING_BASE_URL}/replays',
                                headers=headers,
                                params={'count': 1},
                                timeout=10)

        if response.status_code == 200:
            print('✅ Ballchasing API connection successful!')
        elif response.status_code == 401:
            print('❌ Ballchasing API key invalid')
        else:
            print(f'❌ API connection failed. Status code: {response.status_code}')
            print(f'Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ API test failed: {str(e)}')


def get_detailed_replay(replay_id, headers):
    """Fetch detailed replay data including full stats"""
    try:
        response = requests.get(f'{BALLCHASING_BASE_URL}/replays/{replay_id}',
                                headers=headers,
                                timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f'Error fetching detailed replay {replay_id}: {e}')
    return None


def find_player_in_detailed_replay(replay_data, steam_id):
    """Find player in detailed replay data with full stats"""
    if not replay_data:
        return None

    # Check both team colors
    for team_color in ['blue', 'orange']:
        team_data = replay_data.get(team_color)
        if not team_data or 'players' not in team_data:
            continue

        for player in team_data['players']:
            # Handle different ID formats
            player_id_data = player.get('id', {})

            if isinstance(player_id_data, dict):
                player_id = player_id_data.get('id', '')
            else:
                player_id = str(player_id_data)

            # Clean the player ID for comparison
            clean_player_id = player_id.replace('steam:', '')

            if clean_player_id == steam_id or steam_id in player_id:
                return {
                    'player': player,
                    'team_color': team_color,
                    'team_data': team_data
                }
    return None


def find_player_in_replay(replay, steam_id):
    """Helper function to find a player in a replay and return their data"""
    for team_color in ['blue', 'orange']:
        if team_color in replay and 'players' in replay[team_color]:
            for player in replay[team_color]['players']:
                # Get player ID - handle different formats
                player_id_data = player.get('id', {})

                if isinstance(player_id_data, dict):
                    player_actual_id = player_id_data.get('id', '')
                else:
                    player_actual_id = str(player_id_data)

                # Check if this is our player (handle both formats)
                if player_actual_id == steam_id or player_actual_id == f'steam:{steam_id}' or steam_id in player_actual_id:
                    return {
                        'player': player,
                        'team_color': team_color,
                        'team_data': replay[team_color]
                    }
    return None


def check_player_won(replay, steam_id):
    """Helper function to check if player won the match"""
    player_data = find_player_in_replay(replay, steam_id)
    if not player_data:
        return False

    team_color = player_data['team_color']

    # Get team scores
    blue_score = replay.get('blue', {}).get('goals', 0) or replay.get('blue_score', 0)
    orange_score = replay.get('orange', {}).get('goals', 0) or replay.get('orange_score', 0)

    if team_color == 'blue':
        return blue_score > orange_score
    else:
        return orange_score > blue_score


@bot.command()
async def hello(ctx):
    """Basic test command"""
    await ctx.send('🚗💨 RL Stats Bot is online! Using Ballchasing.com API for replay analysis!')


@bot.command()
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Bot latency: {latency}ms')


@bot.command()
async def test_api(ctx):
    """Test the Ballchasing API connection"""
    await ctx.send('🔍 Testing Ballchasing API connection...')

    headers = {
        'Authorization': BALLCHASING_API_KEY
    }

    try:
        # Test with a simple replays query
        response = requests.get(f'{BALLCHASING_BASE_URL}/replays',
                                headers=headers,
                                params={'count': 1},
                                timeout=10)

        if response.status_code == 200:
            data = response.json()
            total_replays = data.get('count', 0)
            await ctx.send(f'✅ API working! Total replays in database: **{total_replays:,}**')
        elif response.status_code == 401:
            await ctx.send('❌ API key invalid. Check your Ballchasing.com API key.')
        elif response.status_code == 429:
            await ctx.send('⏳ API rate limit hit. Try again in a minute.')
        else:
            await ctx.send(f'❌ API error. Status code: {response.status_code}')

    except requests.exceptions.Timeout:
        await ctx.send('⏰ API request timed out. Try again.')
    except Exception as e:
        await ctx.send(f'❌ Error testing API: {str(e)}')


@bot.command()
async def player_stats(ctx, steam_id=''):
    """Get comprehensive player stats from uploaded replays"""
    if not steam_id:
        await ctx.send('❌ Please provide a Steam ID! Example: `!player_stats 76561198034830043`')
        return

    # Clean the steam ID input
    steam_id = steam_id.replace('steam:', '').strip()

    await ctx.send(f'🔍 Analyzing replays for Steam ID: {steam_id}... This may take a moment.')

    headers = {
        'Authorization': BALLCHASING_API_KEY
    }

    try:
        # Get replays for this player - try different formats
        response = requests.get(f'{BALLCHASING_BASE_URL}/replays',
                                headers=headers,
                                params={
                                    'player-id': f'steam:{steam_id}',
                                    'count': 25  # Reduced count to avoid rate limits
                                },
                                timeout=15)

        # If first format doesn't work, try without steam: prefix
        if response.status_code != 200:
            response = requests.get(f'{BALLCHASING_BASE_URL}/replays',
                                    headers=headers,
                                    params={
                                        'player-id': steam_id,
                                        'count': 25
                                    },
                                    timeout=15)

        if response.status_code == 200:
            data = response.json()
            replays = data.get('list', [])

            if not replays:
                await ctx.send(
                    f'❌ No replays found for Steam ID: {steam_id}\n💡 Player needs to upload replays to ballchasing.com first!')
                return

            # Progress update
            await ctx.send(f'📊 Found {len(replays)} replays, fetching detailed stats...')

            # Enhanced analysis with detailed replay data
            total_games = len(replays)
            wins = 0
            total_score = 0
            total_goals = 0
            total_saves = 0
            total_assists = 0
            total_shots = 0
            total_demos = 0
            mvp_count = 0

            playlists = {}  # Track different game modes
            player_name = "Unknown"
            processed_games = 0

            for i, replay in enumerate(replays):
                playlist = replay.get('playlist_name', 'Unknown')
                if playlist not in playlists:
                    playlists[playlist] = {'games': 0, 'wins': 0}
                playlists[playlist]['games'] += 1

                # Get detailed replay data for accurate stats
                detailed_replay = get_detailed_replay(replay.get('id'), headers)

                if detailed_replay:
                    # Find the player in detailed replay
                    player_data = find_player_in_detailed_replay(detailed_replay, steam_id)

                    if player_data:
                        player = player_data['player']
                        processed_games += 1

                        # Get player name (first time we find them)
                        if player_name == "Unknown":
                            player_name = player.get('name', 'Unknown')

                        # Extract stats from detailed data
                        stats = player.get('stats', {})
                        if isinstance(stats, dict):
                            # Core stats
                            core_stats = stats.get('core', {})
                            if isinstance(core_stats, dict):
                                total_score += core_stats.get('score', 0)
                                total_goals += core_stats.get('goals', 0)
                                total_saves += core_stats.get('saves', 0)
                                total_assists += core_stats.get('assists', 0)
                                total_shots += core_stats.get('shots', 0)

                                # Check MVP
                                if core_stats.get('mvp', False):
                                    mvp_count += 1

                            # Demo stats
                            demo_stats = stats.get('demo', {})
                            if isinstance(demo_stats, dict):
                                total_demos += demo_stats.get('inflicted', 0)

                        # Check win/loss using detailed data
                        blue_score = detailed_replay.get('blue', {}).get('goals', 0)
                        orange_score = detailed_replay.get('orange', {}).get('goals', 0)
                        team_color = player_data['team_color']

                        if (team_color == 'blue' and blue_score > orange_score) or \
                                (team_color == 'orange' and orange_score > blue_score):
                            wins += 1
                            playlists[playlist]['wins'] += 1
                else:
                    # Fallback to basic replay data if detailed fetch fails
                    player_data = find_player_in_replay(replay, steam_id)
                    if player_data:
                        processed_games += 1
                        if player_name == "Unknown":
                            player_name = player_data['player'].get('name', 'Unknown')

                        if check_player_won(replay, steam_id):
                            wins += 1
                            playlists[playlist]['wins'] += 1

                # Add small delay to avoid rate limiting
                if i % 5 == 0:
                    await asyncio.sleep(0.5)

            if processed_games == 0:
                await ctx.send(
                    '❌ Could not process any replay data. Player might not be in the replays or there was an API issue.')
                return

            # Calculate enhanced stats
            avg_score = total_score / processed_games if processed_games > 0 else 0
            avg_goals = total_goals / processed_games if processed_games > 0 else 0
            avg_saves = total_saves / processed_games if processed_games > 0 else 0
            avg_assists = total_assists / processed_games if processed_games > 0 else 0
            avg_shots = total_shots / processed_games if processed_games > 0 else 0
            avg_demos = total_demos / processed_games if processed_games > 0 else 0
            win_rate = (wins / processed_games * 100) if processed_games > 0 else 0
            mvp_rate = (mvp_count / processed_games * 100) if processed_games > 0 else 0
            shot_accuracy = (total_goals / total_shots * 100) if total_shots > 0 else 0

            # Create enhanced embed
            stats_embed = discord.Embed(
                title=f"🚗 {player_name}'s Performance Report",
                description=f"Analysis of **{processed_games}** processed replays (from {total_games} found)",
                color=0x00ff88
            )

            # Main stats
            stats_embed.add_field(name="🏆 Win Rate", value=f"**{win_rate:.1f}%**\n({wins}W-{processed_games - wins}L)",
                                  inline=True)
            stats_embed.add_field(name="⭐ MVP Rate", value=f"**{mvp_rate:.1f}%**\n({mvp_count} MVPs)", inline=True)
            stats_embed.add_field(name="🎯 Shot Accuracy",
                                  value=f"**{shot_accuracy:.1f}%**\n({total_goals}/{total_shots})", inline=True)

            # Performance averages
            stats_embed.add_field(name="📊 Avg Score", value=f"**{avg_score:.0f}**", inline=True)
            stats_embed.add_field(name="⚽ Goals/Game", value=f"**{avg_goals:.1f}**", inline=True)
            stats_embed.add_field(name="🥅 Saves/Game", value=f"**{avg_saves:.1f}**", inline=True)
            stats_embed.add_field(name="🤝 Assists/Game", value=f"**{avg_assists:.1f}**", inline=True)
            stats_embed.add_field(name="🚀 Shots/Game", value=f"**{avg_shots:.1f}**", inline=True)
            stats_embed.add_field(name="💥 Demos/Game", value=f"**{avg_demos:.1f}**", inline=True)

            # Add playlist breakdown if multiple modes
            if len(playlists) > 1:
                playlist_text = ""
                for playlist, data in playlists.items():
                    wr = (data['wins'] / data['games'] * 100) if data['games'] > 0 else 0
                    playlist_text += f"**{playlist}:** {wr:.0f}% ({data['wins']}/{data['games']})\n"

                if playlist_text:
                    stats_embed.add_field(name="🎮 By Playlist", value=playlist_text, inline=False)

            stats_embed.set_footer(
                text="💡 Detailed stats require individual replay fetching - upload more replays for better analysis!")

            await ctx.send(embed=stats_embed)

        elif response.status_code == 404:
            await ctx.send(
                f'❌ Player **{steam_id}** not found or no replays uploaded.\n💡 Make sure they have uploaded replays to ballchasing.com!')
        else:
            await ctx.send(f'❌ Error fetching data. Status code: {response.status_code}')

    except Exception as e:
        await ctx.send(f'❌ Error: {str(e)}')


@bot.command()
async def recent_games(ctx, steam_id='', count=5):
    """Show recent games with detailed results"""
    if not steam_id:
        await ctx.send('❌ Please provide a Steam ID! Example: `!recent_games 76561198034830043 10`')
        return

    # Clean the steam ID and limit count to reasonable number
    steam_id = steam_id.replace('steam:', '').strip()
    count = min(max(count, 1), 15)

    headers = {
        'Authorization': BALLCHASING_API_KEY
    }

    try:
        response = requests.get(f'{BALLCHASING_BASE_URL}/replays',
                                headers=headers,
                                params={
                                    'player-id': f'steam:{steam_id}',
                                    'count': count
                                },
                                timeout=15)

        if response.status_code == 200:
            data = response.json()
            replays = data.get('list', [])

            if not replays:
                await ctx.send(f'❌ No recent games found for Steam ID: {steam_id}')
                return

            # Progress message
            await ctx.send(f'🔍 Fetching detailed stats for {len(replays)} recent games...')

            # Get player name from first replay
            player_name = "Unknown"

            embed = discord.Embed(
                title=f"🎮 Recent Games",
                description=f"Loading detailed stats...",
                color=0x0099ff
            )

            games_text = ""
            win_streak = 0
            current_streak = 0
            last_result = None
            recent_wins = 0

            for i, replay in enumerate(replays[:count], 1):
                date = replay.get('date', 'Unknown')[:10]  # Just the date part
                playlist = replay.get('playlist_name', 'Unknown')

                # Get detailed replay for accurate stats
                detailed_replay = get_detailed_replay(replay.get('id'), headers)

                if detailed_replay:
                    blue_score = detailed_replay.get('blue', {}).get('goals', 0)
                    orange_score = detailed_replay.get('orange', {}).get('goals', 0)

                    # Find player's detailed performance
                    player_data = find_player_in_detailed_replay(detailed_replay, steam_id)

                    if player_data:
                        player = player_data['player']
                        team_color = player_data['team_color']

                        if player_name == "Unknown":
                            player_name = player.get('name', 'Unknown')

                        # Check if player won
                        player_won = (team_color == 'blue' and blue_score > orange_score) or \
                                     (team_color == 'orange' and orange_score > blue_score)

                        if player_won:
                            recent_wins += 1

                        # Track win streak
                        if player_won:
                            if last_result == 'W':
                                current_streak += 1
                            else:
                                current_streak = 1
                            last_result = 'W'
                        else:
                            if last_result == 'L':
                                current_streak += 1
                            else:
                                current_streak = 1
                            last_result = 'L'

                        win_streak = max(win_streak, current_streak if player_won else 0)

                        # Get detailed stats
                        stats = player.get('stats', {}).get('core', {})
                        result_emoji = "✅" if player_won else "❌"
                        score = f"{blue_score}-{orange_score}"

                        if stats:
                            player_score = stats.get('score', 0)
                            goals = stats.get('goals', 0)
                            saves = stats.get('saves', 0)
                            assists = stats.get('assists', 0)

                            games_text += f"{result_emoji} **{score}** | {player_score}pts ({goals}G {saves}S {assists}A)\n"
                        else:
                            games_text += f"{result_emoji} **{score}** | {playlist}\n"
                else:
                    # Fallback to basic data
                    blue_score = replay.get('blue', {}).get('goals', 0) or replay.get('blue_score', 0)
                    orange_score = replay.get('orange', {}).get('goals', 0) or replay.get('orange_score', 0)

                    player_data = find_player_in_replay(replay, steam_id)
                    if player_data and player_name == "Unknown":
                        player_name = player_data['player'].get('name', 'Unknown')

                    player_won = check_player_won(replay, steam_id)
                    if player_won:
                        recent_wins += 1

                    result_emoji = "✅" if player_won else "❌"
                    score = f"{blue_score}-{orange_score}"
                    games_text += f"{result_emoji} **{score}** | {playlist}\n"

                # Small delay to avoid rate limiting
                if i % 3 == 0:
                    await asyncio.sleep(0.3)

            # Update embed with final data
            embed.title = f"🎮 {player_name}'s Recent Games"
            embed.description = f"Last {len(replays)} matches"

            embed.add_field(name="Recent Results", value=games_text if games_text else "No games found", inline=False)

            if win_streak > 0:
                embed.add_field(name="🔥 Best Win Streak", value=f"{win_streak} games", inline=True)

            # Calculate recent win rate
            recent_wr = (recent_wins / len(replays) * 100) if replays else 0
            embed.add_field(name="📈 Recent Win Rate", value=f"{recent_wr:.0f}%", inline=True)

            await ctx.send(embed=embed)

        else:
            await ctx.send(f'❌ Error fetching recent games. Status: {response.status_code}')

    except Exception as e:
        await ctx.send(f'❌ Error: {str(e)}')


@bot.command()
async def find_steam_id(ctx, *, steam_name_or_url=''):
    """Help users find their Steam ID"""
    if not steam_name_or_url:
        embed = discord.Embed(
            title="🔍 How to Find Your Steam ID",
            description="You need your Steam ID (not display name) to use this bot",
            color=0xffa500
        )

        embed.add_field(
            name="Method 1: steamidfinder.com",
            value="1. Go to **steamidfinder.com**\n2. Enter your Steam name or profile URL\n3. Copy the **steamID64** number",
            inline=False
        )

        embed.add_field(
            name="Method 2: Steam Profile URL",
            value="If your URL is: `steamcommunity.com/profiles/76561198034830043/`\nYour Steam ID is: `76561198034830043`",
            inline=False
        )

        embed.add_field(
            name="Method 3: Custom URL",
            value="If your URL is: `steamcommunity.com/id/yourname/`\nUse steamidfinder.com to convert it",
            inline=False
        )

        embed.add_field(
            name="Example Usage",
            value="`!player_stats 76561198034830043`\n`!recent_games 76561198034830043`",
            inline=False
        )

        embed.set_footer(text="💡 Your Steam ID is a long number, not your display name!")
        await ctx.send(embed=embed)
    else:
        # Give specific guidance for the provided input
        await ctx.send(f"""
🔍 **Looking for Steam ID for:** `{steam_name_or_url}`

**Next steps:**
1. Go to **steamidfinder.com**
2. Paste: `{steam_name_or_url}`
3. Copy the **steamID64** number (looks like: 76561198034830043)
4. Use: `!player_stats THAT_NUMBER`

**Note:** Steam display names change, but Steam IDs are permanent!
        """)


@bot.command()
async def debug_player(ctx, steam_id=''):
    """Debug command to see raw replay data for a player"""
    if not steam_id:
        await ctx.send('❌ Please provide a Steam ID! Example: `!debug_player 76561198034830043`')
        return

    steam_id = steam_id.replace('steam:', '').strip()

    headers = {
        'Authorization': BALLCHASING_API_KEY
    }

    try:
        # Try to get replays
        response = requests.get(f'{BALLCHASING_BASE_URL}/replays',
                                headers=headers,
                                params={
                                    'player-id': f'steam:{steam_id}',
                                    'count': 2
                                },
                                timeout=15)

        await ctx.send(f'🔍 Debug info for Steam ID: {steam_id}')
        await ctx.send(f'📊 API Response Status: {response.status_code}')

        if response.status_code == 200:
            data = response.json()
            replays = data.get('list', [])
            await ctx.send(f'✅ Found {len(replays)} replays')

            if replays:
                # Show structure of first replay
                first_replay = replays[0]
                replay_id = first_replay.get('id')

                await ctx.send(f'📋 Testing detailed replay fetch for ID: {replay_id}')

                # Get detailed replay
                detailed_replay = get_detailed_replay(replay_id, headers)

                if detailed_replay:
                    await ctx.send('✅ **Detailed replay fetch successful!**')

                    blue_goals = detailed_replay.get('blue', {}).get('goals', 'N/A')
                    orange_goals = detailed_replay.get('orange', {}).get('goals', 'N/A')

                    debug_info = f"""
**Detailed Replay Info:**
• ID: {replay_id}
• Date: {detailed_replay.get('date', 'N/A')[:10]}
• Duration: {detailed_replay.get('duration', 0)}s
• Blue Score: {blue_goals}
• Orange Score: {orange_goals}
"""
                    await ctx.send(debug_info)

                    # Check if we can find the player in detailed data
                    player_data = find_player_in_detailed_replay(detailed_replay, steam_id)

                    if player_data:
                        player = player_data['player']
                        team_color = player_data['team_color']
                        await ctx.send(
                            f'✅ **Found player on {team_color} team!**\nName: {player.get("name", "Unknown")}')

                        # Show detailed player stats
                        stats = player.get('stats', {})
                        if isinstance(stats, dict):
                            core_stats = stats.get('core', {})
                            if isinstance(core_stats, dict) and core_stats:
                                stats_text = f"""
**Detailed Player Stats:**
• Score: {core_stats.get('score', 0)}
• Goals: {core_stats.get('goals', 0)}
• Saves: {core_stats.get('saves', 0)}
• Assists: {core_stats.get('assists', 0)}
• Shots: {core_stats.get('shots', 0)}
• MVP: {core_stats.get('mvp', False)}
"""
                                await ctx.send(stats_text)
                            else:
                                await ctx.send('⚠️ Core stats not found or empty')
                        else:
                            await ctx.send('⚠️ Stats object not found or invalid format')
                    else:
                        await ctx.send('❌ **Player not found in detailed replay data!**')
                else:
                    await ctx.send('❌ **Failed to fetch detailed replay data**')

        else:
            await ctx.send(f'❌ API Error: {response.status_code}\nResponse: {response.text[:200]}')

    except Exception as e:
        await ctx.send(f'❌ Debug Error: {str(e)}')


@bot.command(name='help_rl')
async def help_rl(ctx):
    """Show all available commands with examples"""
    embed = discord.Embed(
        title="🚀 RL Stats Bot Commands",
        description="Enhanced version with detailed stats extraction",
        color=0x00ff88
    )

    embed.add_field(
        name="🧪 Test Commands",
        value="`!hello` - Basic bot test\n`!ping` - Check latency\n`!test_api` - Test API connection",
        inline=False
    )

    embed.add_field(
        name="📊 Stats Commands",
        value="`!player_stats STEAM_ID` - Full performance report (enhanced)\n`!recent_games STEAM_ID [count]` - Recent matches with stats\n`!find_steam_id [name]` - Help finding Steam ID",
        inline=False
    )

    embed.add_field(
        name="🔧 Debug Commands",
        value="`!debug_player STEAM_ID` - Debug player data\n`!help_rl` - Show this help message",
        inline=False
    )

    embed.add_field(
        name="💡 Examples",
        value="`!player_stats 76561198034830043`\n`!recent_games 76561198034830043 10`\n`!find_steam_id Kronovi`",
        inline=False
    )
    embed.set_footer(text="Need help finding your Steam ID? Use !find_steam_id")
    await ctx.send(embed=embed)


# Error handling
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


# Run the bot
if __name__ == '__main__':
    print('Starting RL Stats Bot with Ballchasing.com API...')
    print('Note: Players need to upload replays to ballchasing.com first!')
    bot.run('MTQwOTIzMDY4NTU3MDQ2OTg5MQ.Gy5q_C.WGuumk9ZwXoZVUc5oyRQjpFJytO9S2NmNQxg3w')