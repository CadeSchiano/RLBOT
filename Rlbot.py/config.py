import os
from pathlib import Path

# Get the directory where this config.py file is located
BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / '.env'

# Manually parse the .env file (workaround for dotenv issues)
if dotenv_path.exists():
    with open(dotenv_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                # Split on first = only
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Set in environment
                    os.environ[key] = value
DISCORD_TOKEN = os.getenv('MTQwOTIzMDY4NTU3MDQ2OTg5MQ.GL9gW3.PostVBAwltdkQYIiG-SLyfYimCqBwvzFeuVHzY')


# RapidAPI Key for Rocket League API
RAPIDAPI_KEY = os.getenv('401899db29msh9edc353bdb9bd39p1b5581jsn38884637372b')

RAPIDAPI_HOST = "rocket-league1.p.rapidapi.com"

# Validate that required environment variables are set
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables!")

if not RAPIDAPI_KEY:
    raise ValueError("RAPIDAPI_KEY not found in environment variables!")