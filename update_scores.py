import requests
import json
import os

# Reusing the existing secret name so you don't have to change your .yml file
API_KEY = os.environ.get("API_FOOTBALL_KEY") 
DATA_FILE = "data.json"
COMPETITION_ID = "2000" # Football-Data.org's ID for the FIFA World Cup

# Maps the API's stage names to the exact round names used in your app's scoring logic
ROUND_MAP = {
    "LAST_32": "Round of 32",
    "LAST_16": "Round of 16",
    "QUARTER_FINALS": "Quarter-finals",
    "SEMI_FINALS": "Semi-finals",
    "FINAL": "Final"
}

def get_live_scores():
    url = f"https://api.football-data.org/v4/competitions/{COMPETITION_ID}/matches"
    headers = {
        'X-Auth-Token': API_KEY
    }
    response = requests.get(url, headers=headers)
    
    try:
        data = response.json()
        print("API Response fetched successfully.")
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
    
    if "matches" in api_data:
        for match in api_data["matches"]:
            raw_stage = match.get("stage", "")
            
            # Filter to only process knockout rounds
            if raw_stage not in ROUND_MAP:
                continue
                
            match_id = str(match["id"])
            status = match["status"]
            
            # Map the API's "FINISHED" status to the phrase your Streamlit app expects
            app_status = "Match Finished" if status == "FINISHED" else status
            
            # Safely get team names, defaulting to "TBD" if they aren't decided yet
            home_node = match.get("homeTeam") or {}
            away_node = match.get("awayTeam") or {}
            home_team = home_node.get("name") or "TBD"
            away_team = away_node.get("name") or "TBD"
            
            winner = None
            if status == "FINISHED":
                api_winner = match["score"].get("winner")
                if api_winner == "HOME_TEAM":
                    winner = home_team
                elif api_winner == "AWAY_TEAM":
                    winner = away_team

            data["matches"][match_id] = {
                "team_home": home_team,
                "team_away": away_team,
                "kickoff_utc": match["utcDate"],
                "status": app_status,
                "winner": winner,
                "round": ROUND_MAP[raw_stage]
            }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print("Script execution completed successfully.")

if __name__ == "__main__":
    update_data()
