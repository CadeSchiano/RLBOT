import discord
from discord.ext import commands
import requests
import asyncio
from config import BALLCHASING_API_KEY
from utils import get_detailed_replay, find_player_in_detailed_replay, find_player_in_replay, check_player_won

BALLCHASING_BASE_URL = 'https://ballchasing.com/api'

def setup_commands(bot):
    @bot.command()
    async def hello(ctx):
        await ctx.send('🚗💨 RL Stats Bot is online! Using Ballchasing.com API for replay analysis!')

    @bot.command()
    async def ping(ctx):
        latency = round(bot.latency * 1000)
        await ctx.send(f'🏓 Pong! Bot latency: {latency}ms')

    @bot.command()
    async def test_api(ctx):
        await ctx.send('🔍 Testing Ballchasing API connection...')
        headers = {'Authorization': BALLCHASING_API_KEY}
        try:
            response = requests.get(f'{BALLCHASING_BASE_URL}/replays', headers=headers, params={'count': 1}, timeout=10)
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
        if not steam_id:
            await ctx.send('❌ Please provide a Steam ID! Example: `!player_stats 76561198034830043`')
            return

        steam_id = steam_id.replace('steam:', '').strip()
        await ctx.send(f'🔍 Analyzing replays for Steam ID: {steam_id}... This may take a moment.')
        headers = {'Authorization': BALLCHASING_API_KEY}
        try:
            response = requests.get(f'{BALLCHASING_BASE_URL}/replays', headers=headers, params={'player-id': f'steam:{steam_id}', 'count': 25}, timeout=15)
            if response.status_code != 200:
                response = requests.get(f'{BALLCHASING_BASE_URL}/replays', headers=headers, params={'player-id': steam_id, 'count': 25}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                replays = data.get('list', [])
                if not replays:
                    await ctx.send(f'❌ No replays found for Steam ID: {steam_id}\n💡 Player needs to upload replays to ballchasing.com first!')
                    return
                await ctx.send(f'📊 Found {len(replays)} replays, fetching detailed stats...')
                total_games = len(replays)
                wins = total_score = total_goals = total_saves = total_assists = total_shots = total_demos = mvp_count = 0
                playlists = {}
                player_name = "Unknown"
                processed_games = 0
                for i, replay in enumerate(replays):
                    playlist = replay.get('playlist_name', 'Unknown')
                    if playlist not in playlists:
                        playlists[playlist] = {'games': 0, 'wins': 0}
                    playlists[playlist]['games'] += 1
                    detailed_replay = get_detailed_replay(replay.get('id'), headers)
                    if detailed_replay:
                        player_data = find_player_in_detailed_replay(detailed_replay, steam_id)
                        if player_data:
                            player = player_data['player']
                            processed_games += 1
                            if player_name == "Unknown":
                                player_name = player.get('name', 'Unknown')
                            stats = player.get('stats', {})
                            if isinstance(stats, dict):
                                core_stats = stats.get('core', {})
                                if isinstance(core_stats, dict):
                                    total_score += core_stats.get('score', 0)
                                    total_goals += core_stats.get('goals', 0)
                                    total_saves += core_stats.get('saves', 0)
                                    total_assists += core_stats.get('assists', 0)
                                    total_shots += core_stats.get('shots', 0)
                                    if core_stats.get('mvp', False):
                                        mvp_count += 1
                                demo_stats = stats.get('demo', {})
                                if isinstance(demo_stats, dict):
                                    total_demos += demo_stats.get('inflicted', 0)
                            blue_score = detailed_replay.get('blue', {}).get('goals', 0)
                            orange_score = detailed_replay.get('orange', {}).get('goals', 0)
                            team_color = player_data['team_color']
                            if (team_color == 'blue' and blue_score > orange_score) or (team_color == 'orange' and orange_score > blue_score):
                                wins += 1
                                playlists[playlist]['wins'] += 1
                    else:
                        player_data = find_player_in_replay(replay, steam_id)
                        if player_data:
                            processed_games += 1
                            if player_name == "Unknown":
                                player_name = player_data['player'].get('name', 'Unknown')
                            if check_player_won(replay, steam_id):
                                wins += 1
                                playlists[playlist]['wins'] += 1
                    if i % 5 == 0:
                        await asyncio.sleep(0.5)
                if processed_games == 0:
                    await ctx.send('❌ Could not process any replay data. Player might not be in the replays or there was an API issue.')
                    return
                avg_score = total_score / processed_games if processed_games > 0 else 0
                avg_goals = total_goals / processed_games if processed_games > 0 else 0
                avg_saves = total_saves / processed_games if processed_games > 0 else 0
                avg_assists = total_assists / processed_games if processed_games > 0 else 0
                avg_shots = total_shots / processed_games if processed_games > 0 else 0
                avg_demos = total_demos / processed_games if processed_games > 0 else 0
                win_rate = (wins / processed_games * 100) if processed_games > 0 else 0
                mvp_rate = (mvp_count / processed_games * 100) if processed_games > 0 else 0
                shot_accuracy = (total_goals / total_shots * 100) if total_shots > 0 else 0
                stats_embed = discord.Embed(
                    title=f"🚗 {player_name}'s Performance Report",
                    description=f"Analysis of **{processed_games}** processed replays (from {total_games} found)",
                    color=0x00ff88
                )
                stats_embed.add_field(name="🏆 Win Rate", value=f"**{win_rate:.1f}%**\n({wins}W-{processed_games - wins}L)", inline=True)
                stats_embed.add_field(name="⭐ MVP Rate", value=f"**{mvp_rate:.1f}%**\n({mvp_count} MVPs)", inline=True)
                stats_embed.add_field(name="🎯 Shot Accuracy", value=f"**{shot_accuracy:.1f}%**\n({total_goals}/{total_shots})", inline=True)
                stats_embed.add_field(name="📊 Avg Score", value=f"**{avg_score:.0f}**", inline=True)
                stats_embed.add_field(name="⚽ Goals/Game", value=f"**{avg_goals:.1f}**", inline=True)
                stats_embed.add_field(name="🥅 Saves/Game", value=f"**{avg_saves:.1f}**", inline=True)
                stats_embed.add_field(name="🤝 Assists/Game", value=f"**{avg_assists:.1f}**", inline=True)
                stats_embed.add_field(name="🚀 Shots/Game", value=f"**{avg_shots:.1f}**", inline=True)
                stats_embed.add_field(name="💥 Demos/Game", value=f"**{avg_demos:.1f}**", inline=True)
                if len(playlists) > 1:
                    playlist_text = ""
                    for playlist, data in playlists.items():
                        wr = (data['wins'] / data['games'] * 100) if data['games'] > 0 else 0
                        playlist_text += f"**{playlist}:** {wr:.0f}% ({data['wins']}/{data['games']})\n"
                    if playlist_text:
                        stats_embed.add_field(name="🎮 By Playlist", value=playlist_text, inline=False)
                stats_embed.set_footer(text="💡 Detailed stats require individual replay fetching - upload more replays for better analysis!")
                await ctx.send(embed=stats_embed)
            elif response.status_code == 404:
                await ctx.send(f'❌ Player **{steam_id}** not found or no replays uploaded.\n💡 Make sure they have uploaded replays to ballchasing.com!')
            else:
                await ctx.send(f'❌ Error fetching data. Status code: {response.status_code}')
        except Exception as e:
            await ctx.send(f'❌ Error: {str(e)}')

    @bot.command()
    async def recent_games(ctx, steam_id='', count=5):
        if not steam_id:
            await ctx.send('❌ Please provide a Steam ID! Example: `!recent_games 76561198034830043 10`')
            return
        steam_id = steam_id.replace('steam:', '').strip()
        count = min(max(count, 1), 15)
        headers = {'Authorization': BALLCHASING_API_KEY}
        try:
            response = requests.get(f'{BALLCHASING_BASE_URL}/replays', headers=headers, params={'player-id': f'steam:{steam_id}', 'count': count}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                replays = data.get('list', [])
                if not replays:
                    await ctx.send(f'❌ No recent games found for Steam ID: {steam_id}')
                    return
                await ctx.send(f'🔍 Fetching detailed stats for {len(replays)} recent games...')
                player_name = "Unknown"
                embed = discord.Embed(title=f"🎮 Recent Games", description=f"Loading detailed stats...", color=0x0099ff)
                games_text = ""
                win_streak = 0
                current_streak = 0
                last_result = None
                recent_wins = 0
                for i, replay in enumerate(replays[:count], 1):
                    date = replay.get('date', 'Unknown')[:10]
                    playlist = replay.get('playlist_name', 'Unknown')
                    detailed_replay = get_detailed_replay(replay.get('id'), headers)
                    if detailed_replay:
                        blue_score = detailed_replay.get('blue', {}).get('goals', 0)
                        orange_score = detailed_replay.get('orange', {}).get('goals', 0)
                        player_data = find_player_in_detailed_replay(detailed_replay, steam_id)
                        if player_data:
                            player = player_data['player']
                            team_color = player_data['team_color']
                            if player_name == "Unknown":
                                player_name = player.get('name', 'Unknown')
                            player_won = (team_color == 'blue' and blue_score > orange_score) or (team_color == 'orange' and orange_score > blue_score)
                            if player_won:
                                recent_wins += 1
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
                    if i % 3 == 0:
                        await asyncio.sleep(0.3)
                embed.title = f"🎮 {player_name}'s Recent Games"
                embed.description = f"Last {len(replays)} matches"
                embed.add_field(name="Recent Results", value=games_text if games_text else "No games found", inline=False)
                if win_streak > 0:
                    embed.add_field(name="🔥 Best Win Streak", value=f"{win_streak} games", inline=True)
                recent_wr = (recent_wins / len(replays) * 100) if replays else 0
                embed.add_field(name="📈 Recent Win Rate", value=f"{recent_wr:.0f}%", inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f'❌ Error fetching recent games. Status: {response.status_code}')
        except Exception as e:
            await ctx.send(f'❌ Error: {str(e)}')

    @bot.command()
    async def find_steam_id(ctx, *, steam_name_or_url=''):
        if not steam_name_or_url:
            embed = discord.Embed(
                title="🔍 How to Find Your Steam ID",
                description="You need your Steam ID (not display name) to use this bot",
                color=5B2071
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
        if not steam_id:
            await ctx.send('❌ Please provide a Steam ID! Example: `!debug_player 76561198034830043`')
            return
        steam_id = steam_id.replace('steam:', '').strip()
        headers = {'Authorization': BALLCHASING_API_KEY}
        try:
            response = requests.get(f'{BALLCHASING_BASE_URL}/replays', headers=headers, params={'player-id': f'steam:{steam_id}', 'count': 2}, timeout=15)
            await ctx.send(f'🔍 Debug info for Steam ID: {steam_id}')
            await ctx.send(f'📊 API Response Status: {response.status_code}')
            if response.status_code == 200:
                data = response.json()
                replays = data.get('list', [])
                await ctx.send(f'✅ Found {len(replays)} replays')
                if replays:
                    first_replay = replays[0]
                    replay_id = first_replay.get('id')
                    await ctx.send(f'📋 Testing detailed replay fetch for ID: {replay_id}')
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
                        player_data = find_player_in_detailed_replay(detailed_replay, steam_id)
                        if player_data:
                            player = player_data['player']
                            team_color = player_data['team_color']
                            await ctx.send(f'✅ **Found player on {team_color} team!**\nName: {player.get("name", "Unknown")}')
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
