# RL Stats Bot Setup Instructions

## Prerequisites
- Python 3.8 or higher
- A Discord account
- A RapidAPI account

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Get Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Under "Token", click "Reset Token" and copy it (keep this secret!)
6. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent (optional)

## Step 3: Get Your RapidAPI Key

1. Go to [RapidAPI](https://rapidapi.com/)
2. Sign up for a free account (or log in)
3. Visit the [Rocket League API page](https://rapidapi.com/rocket-league-rocket-league-default/api/rocket-league1)
4. Click "Subscribe to Test" button
5. Choose a plan (Free tier available with 500 requests/month)
6. Once subscribed, go to the "Endpoints" tab
7. Your API key will be shown in the code snippets as "X-RapidAPI-Key"
8. Copy this key (keep this secret!)

## Step 4: Configure Your Bot

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and add your keys:
   ```
   DISCORD_TOKEN=your_actual_discord_token_here
   RAPIDAPI_KEY=your_actual_rapidapi_key_here
   ```

## Step 5: Invite Bot to Your Server

1. Go back to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to "OAuth2" → "URL Generator"
4. Select scopes:
   - `bot`
   - `applications.commands`
5. Select bot permissions:
   - Send Messages
   - Embed Links
   - Read Message History
6. Copy the generated URL and open it in your browser
7. Select your server and authorize

## Step 6: Run Your Bot

```bash
python bot.py
```

You should see:
```
Starting RL Stats Bot with RapidAPI...
🚀 YourBotName is online and ready!
Connected to X servers
```

## Testing Your Bot

In your Discord server, try these commands:

```
!hello
!ping
!test_api
!player_stats epic Forky
!population
!help_rl
```

## Important Notes

- **Never share your `.env` file or commit it to Git!**
- Add `.env` to your `.gitignore` file
- The free tier of RapidAPI gives you 500 requests per month
- Player lookups require exact usernames (case-sensitive)
- Supported platforms: **epic**, **steam**, **ps4**, **xboxone**

## Troubleshooting

### "DISCORD_TOKEN not found"
- Make sure your `.env` file exists and contains the token
- Check that there are no extra spaces or quotes around the token

### "RAPIDAPI_KEY not found"
- Make sure you subscribed to the Rocket League API on RapidAPI
- Copy the key from the "X-RapidAPI-Key" header in the code snippets
- The key should be in your `.env` file

### "Status code: 429" (Rate Limit)
- You've exceeded your monthly request limit
- Upgrade your RapidAPI plan or wait until next month
- Free tier: 500 requests/month

### "Player not found"
- Make sure you're using the correct platform (epic, steam, ps4, xboxone)
- Usernames are case-sensitive - use exact spelling
- Some players may have special characters in their names

### Bot doesn't respond
- Check that Message Content Intent is enabled in Discord Developer Portal
- Make sure the bot has permission to send messages in your server
- Verify the bot is online (check the status in your server)