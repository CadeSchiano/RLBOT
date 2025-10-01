

# RLBOT

RLBOT is a Discord bot for tracking your Rocket League stats (Steam only) using the Ballchasing.com API.

## Features
- Track winrate, total goals, assists, saves, demos, and averages per game
- View recent match results and streaks
- Get help finding your Steam ID
- Debug replay data

## Setup
1. Clone this repository.
2. Install dependencies:
	```bash
	pip install -r Rlbot.py/requirements.txt
	```
3. Create a `config.py` file in `Rlbot.py/` with your Discord bot token and Ballchasing API key. See `config_template.py` for the format.
4. Run the bot:
	```bash
	python3 Rlbot.py/bot.py
	```

## Usage
Invite the bot to your server and use the following commands:

- `!hello` — Test if the bot is online
- `!ping` — Check bot latency
- `!player_stats <STEAM_ID>` — Get full performance report
- `!recent_games <STEAM_ID> [count]` — Show recent matches
- `!find_steam_id [name or url]` — Help finding your Steam ID
- `!debug_player <STEAM_ID>` — Debug player data
- `!help_rl` — Show all commands

**Note:** Players must upload replays to [ballchasing.com](https://ballchasing.com/) for stats to be available.





