import requests
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

def get_player_data(platform, player_id):
    """
    Fetch player data from RapidAPI Rocket League API
    
    Args:
        platform (str): Player's platform (epic, steam, ps4, xboxone)
        player_id (str): Player's username
    
    Returns:
        dict: Player data or None if request fails
    """
    url = f"https://{RAPIDAPI_HOST}/player/{platform}/{player_id}"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error fetching player data: {response.status_code}')
            return None
    except Exception as e:
        print(f'Exception fetching player data: {e}')
        return None

def get_population_data():
    """
    Fetch current playlist population data
    
    Returns:
        dict: Population data or None if request fails
    """
    url = f"https://{RAPIDAPI_HOST}/population"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error fetching population data: {response.status_code}')
            return None
    except Exception as e:
        print(f'Exception fetching population data: {e}')
        return None

def format_rank(tier, division):
    """
    Format rank tier and division into readable string
    
    Args:
        tier (str): Rank tier (e.g., "Champion I")
        division (int): Division number (0-3)
    
    Returns:
        str: Formatted rank string
    """
    if not tier:
        return "Unranked"
    return f"{tier} Div {division}"

def calculate_win_rate(wins, total_matches):
    """
    Calculate win rate percentage
    
    Args:
        wins (int): Number of wins
        total_matches (int): Total matches played
    
    Returns:
        float: Win rate percentage (0-100)
    """
    if total_matches == 0:
        return 0.0
    return (wins / total_matches) * 100