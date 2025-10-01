import requests
from config import BALLCHASING_API_KEY


BALLCHASING_BASE_URL = 'https://ballchasing.com/api'

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
    for team_color in ['blue', 'orange']:
        team_data = replay_data.get(team_color)
        if not team_data or 'players' not in team_data:
            continue
        for player in team_data['players']:
            player_id_data = player.get('id', {})
            if isinstance(player_id_data, dict):
                player_id = player_id_data.get('id', '')
            else:
                player_id = str(player_id_data)
            clean_player_id = player_id.replace('steam:', '')
            if clean_player_id == steam_id or steam_id in player_id:
                return {
                    'player': player,
                    'team_color': team_color,
                    'team_data': team_data
                }
    return None

def find_player_in_replay(replay, steam_id):
    for team_color in ['blue', 'orange']:
        if team_color in replay and 'players' in replay[team_color]:
            for player in replay[team_color]['players']:
                player_id_data = player.get('id', {})
                if isinstance(player_id_data, dict):
                    player_actual_id = player_id_data.get('id', '')
                else:
                    player_actual_id = str(player_id_data)
                if player_actual_id == steam_id or player_actual_id == f'steam:{steam_id}' or steam_id in player_actual_id:
                    return {
                        'player': player,
                        'team_color': team_color,
                        'team_data': replay[team_color]
                    }
    return None

def check_player_won(replay, steam_id):
    player_data = find_player_in_replay(replay, steam_id)
    if not player_data:
        return False
    team_color = player_data['team_color']
    blue_score = replay.get('blue', {}).get('goals', 0) or replay.get('blue_score', 0)
    orange_score = replay.get('orange', {}).get('goals', 0) or replay.get('orange_score', 0)
    if team_color == 'blue':
        return blue_score > orange_score
    else:
        return orange_score > blue_score
