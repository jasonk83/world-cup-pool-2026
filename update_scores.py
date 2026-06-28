import requests
import json
import os

API_KEY = os.environ.get("API_FOOTBALL_KEY")
DATA_FILE = "data.json"
LEAGUE_ID = "1"
SEASON = "2026"

def get_live_scores():
    url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}"
    headers = {
        'x-apisports-key': API_KEY
    }
    response = requests.get(url, headers=headers)
    
    # Safely attempt to parse JSON, printing the raw response if it fails
    try:
        data = response.json()
        print("API Response:", data)
        return data
    except requests.exceptions.JSONDecodeError:
        print("CRITICAL API ERROR. Raw response text:")
        print(response.text)
        return {}

def update_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"matches": {}, "picks": {}, "tiebreakers": {}}

    api_data = get_live_scores()
    
    # Check that 'response' exists and is a valid list before looping
    if "response" in api_data and isinstance(api_data["response"], list):
        for fixture in api_data["response"]:
            match_id = str(fixture["fixture"]["id"])
            status = fixture["fixture"]["status"]["long"]
            home_team = fixture["teams"]["home"]["name"]
            away_team = fixture["teams"]["away"]["name"]
            
            winner = None
            if fixture["teams"]["home"]["winner"]:
                winner = home_team
            elif fixture["teams"]["away"]["winner"]:
                winner = away_team

            data["matches"][match_id] = {
                "team_home": home_team,
                "team_away": away_team,
                "kickoff_utc": fixture["fixture"]["date"],
                "status": status,
                "winner": winner,
                "round": fixture["league"]["round"]
            }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print("Script execution completed successfully.")

if __name__ == "__main__":
    update_data()
