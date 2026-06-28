import requests
import json
import os

API_KEY = os.environ.get("API_FOOTBALL_KEY")
DATA_FILE = "data.json"
LEAGUE_ID = "1" # API-Football's standard World Cup ID
SEASON = "2026"

def get_live_scores():
    url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}"
    headers = {
        'x-apisports-key': API_KEY
    }
    response = requests.get(url, headers=headers)
    return response.json()

def update_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        # Initialize structure if it doesn't exist
        data = {"matches": {}, "picks": {}, "tiebreakers": {}}

    api_data = get_live_scores()
    
    if "response" in api_data:
        for fixture in api_data["response"]:
            match_id = str(fixture["fixture"]["id"])
            status = fixture["fixture"]["status"]["long"]
            home_team = fixture["teams"]["home"]["name"]
            away_team = fixture["teams"]["away"]["name"]
            
            # Determine winner
            winner = None
            if fixture["teams"]["home"]["winner"]:
                winner = home_team
            elif fixture["teams"]["away"]["winner"]:
                winner = away_team

            data["matches"][match_id] = {
                "team_home": home_team,
                "team_away": away_team,
                "kickoff_utc": fixture["fixture"]["date"], # UTC ISO format
                "status": status,
                "winner": winner,
                "round": fixture["league"]["round"]
            }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print("Match data updated successfully.")

if __name__ == "__main__":
    update_data()
