import streamlit as st
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import urllib.parse
import base64
import requests

# --- CONFIGURATION (OPTION A: THE DOUBLING METHOD) ---
DATA_FILE = "data.json"
POINTS_MAP = {
    "Round of 32": 2,
    "Round of 16": 4,
    "Quarter-finals": 8,
    "Semi-finals": 16,
    "Final": 32
}

ROUND_ORDER = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Final"
]

# --- FLAG EMOJI MAPPING ---
FLAG_MAP = {
    "Algeria": "🇩🇿", "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Belgium": "🇧🇪", "Bosnia": "🇧🇦", "Bosnia-Herzegovina": "🇧🇦", "Brazil": "🇧🇷", 
    "Cameroon": "🇨🇲", "Canada": "🇨🇦", "Cabo Verde": "🇨🇻", "Cape Verde Islands": "🇨🇻",
    "Chile": "🇨🇱", "Colombia": "🇨🇴", "Costa Rica": "🇨🇷", "Croatia": "🇭🇷", 
    "Democratic Republic of Congo": "🇨🇩", "DR Congo": "🇨🇩", "Congo DR": "🇨🇩",
    "Denmark": "🇩🇰", "Ecuador": "🇪🇨", "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 
    "France": "🇫🇷", "Germany": "🇩🇪", "Ghana": "🇬🇭", "Iran": "🇮🇷", 
    "Italy": "🇮🇹", "Ivory Coast": "🇨🇮", "Japan": "🇯🇵", "Mexico": "🇲🇽", 
    "Morocco": "🇲🇦", "Netherlands": "🇳🇱", "Nigeria": "🇳🇬", "Norway": "🇳🇴", 
    "Paraguay": "🇵🇾", "Peru": "🇵🇪", "Poland": "🇵🇱", "Portugal": "🇵🇹", 
    "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Senegal": "🇸🇳", "Serbia": "🇷🇸",
    "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸", "Sweden": "🇸🇪", 
    "Switzerland": "🇨🇭", "United States": "🇺🇸", "USA": "🇺🇸", "Uruguay": "🇺🇾", 
    "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿"
}

def add_flag(team_name):
    if not team_name or team_name == "TBD":
        return "TBD"
    flag = FLAG_MAP.get(team_name, "")
    return f"{flag} {team_name}".strip()

# --- DATA LOADING & INITIALIZATION ---
def load_data():
    default_players = ["Player 1", "Player 2", "Player 3", "Player 4"]
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "players" not in data:
                data["players"] = default_players
            if "picks" not in data:
                data["picks"] = {p: {} for p in data["players"]}
            if "tiebreakers" not in data:
                data["tiebreakers"] = {p: 0 for p in data["players"]}
            return data
            
    return {
        "players": default_players,
        "matches": {}, 
        "picks": {p: {} for p in default_players}, 
        "tiebreakers": {p: 0 for p in default_players}
    }

def save_data(data):
    # 1. Save locally for an immediate app refresh
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    # 2. Push permanently back to the GitHub repository
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    
    if token and repo:
        url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # GitHub requires the current file's SHA hash to update it
        get_response = requests.get(url, headers=headers)
        if get_response.status_code == 200:
            file_sha = get_response.json().get("sha")
            
            # Encode the new JSON data in Base64 (required by GitHub API)
            json_string = json.dumps(data, indent=4)
            encoded_content = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
            
            payload = {
                "message": "Automated commit: App data updated via Streamlit UI",
                "content": encoded_content,
                "sha": file_sha
            }
            
            # Send the update to GitHub
            requests.put(url, headers=headers, json=payload)

data = load_data()
PLAYERS = data["players"]

st.title("🏆 2026 World Cup Pool")

# --- INSTRUCTIONS ---
st.info("""
Using your unique URL, make your selections for each confirmed matchup before kickoff of the match. Picks are hidden until the match starts and the picks are locked. You can make all the picks at once or go day by day using the URL.

**Scoring Summary**

| Tournament Round | Number of Matchups | Points Per Selection | Total Points Available |
| :--- | :---: | :---: | :---: |
| **Round of 32** | 16 | 2 | 32 |
| **Round of 16** | 8 | 4 | 32 |
| **Quarter-finals** | 4 | 8 | 32 |
| **Semi-finals** | 2 | 16 | 32 |
| **Final** | 1 | 32 | 32 |
""")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["Dashboard & Standings", "Submit Picks", "Manage Pool"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("Current Standings")
    
    scores = {p: 0 for p in PLAYERS}
    for match_id, match_info in data["matches"].items():
        if match_info["status"] == "Match Finished":
            winner_with_flag = add_flag(match_info["winner"])
            round_name = match_info["round"]
            points = POINTS_MAP.get(round_name, 0)
            
            for player in PLAYERS:
                if data["picks"].get(player, {}).get(match_id) == winner_with_flag:
                    scores[player] += points

    st.dataframe([{"Player": p, "Points": s} for p, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)])

    st.divider()
    st.header("Matchups & Picks")
    
    now_utc = datetime.now(timezone.utc)
    
    visible_matches = {
        m_id: m_info for m_id, m_info in data["matches"].items() 
        if m_info['team_home'] != "TBD" and m_info['team_away'] != "TBD"
    }
    
    if not visible_matches:
        st.info("Waiting for upcoming round matchups to be determined.")
    else:
        for current_round in ROUND_ORDER:
            round_matches = {m_id: m_info for m_id, m_info in visible_matches.items() if m_info['round'] == current_round}
            
            if round_matches:
                st.markdown(f"### ⚽ {current_round}")
                st.divider()
                
                for match_id, match_info in round_matches.items():
                    home_team_display = add_flag(match_info['team_home'])
                    away_team_display = add_flag(match_info['team_away'])
                    
                    st.subheader(f"{home_team_display} vs {away_team_display}")
                    
                    kickoff_utc = datetime.fromisoformat(match_info['kickoff_utc'].replace("Z", "+00:00"))
                    kickoff_et = kickoff_utc.astimezone(ZoneInfo("America/New_York")).strftime("%b %d, %I:%M %p ET")
                    kickoff_ct = kickoff_utc.astimezone(ZoneInfo("America/Chicago")).strftime("%I:%M %p CT")
                    
                    st.caption(f"Kickoff: {kickoff_et} / {kickoff_ct}")
                    
                    is_live_or_past = now_utc >= kickoff_utc
                    
                    cols = st.columns(len(PLAYERS) if len(PLAYERS) > 0 else 1)
                    for idx, player in enumerate(PLAYERS):
                        with cols[idx]:
                            pick = data["picks"].get(player, {}).get(match_id, "No Pick")
                            if not is_live_or_past and pick != "No Pick":
                                st.write(f"**{player}**: 🔒 [Hidden]")
                            else:
                                winner_display = add_flag(match_info["winner"]) if match_info.get("winner") else None
                                
                                if match_info["status"] == "Match Finished" and pick == winner_display:
                                    st.success(f"**{player}**: {pick}")
                                elif match_info["status"] == "Match Finished" and pick != winner_display and pick != "No Pick":
                                    st.error(f"**{player}**: {pick}")
                                else:
                                    st.write(f"**{player}**: {pick}")
                    st.write("") 

# --- TAB 2: SUBMIT PICKS ---
with tab2:
    st.header("Submit Your Picks")
    
    url_player = st.query_params.get("player", None)
    
    if not url_player or url_player not in PLAYERS:
        st.error("⚠️ **Access Denied:** You must use your unique personal link to submit picks.")
        st.info("Please request your personalized submission link from the pool administrator.")
    else:
        st.success(f"Verified Entry Session For: **{url_player}**")
        
        player_idx = PLAYERS.index(url_player)
        selected_player = st.selectbox("Your Player Profile:", PLAYERS, index=player_idx, disabled=True)
        
        active_matches = {
            m_id: m_info for m_id, m_info in data["matches"].items()
            if m_info['team_home'] != "TBD" and m_info['team_away'] != "TBD"
        }
        
        if not active_matches:
            st.info("No active matchups available for entry at this moment.")
        else:
            with st.form("picks_form"):
                new_picks = {}
                has_final_round = any(m_info["round"] == "Final" for m_info in active_matches.values())
                
                tiebreaker = 0
                if has_final_round:
                    st.subheader("🏁 Final Match Tiebreaker")
                    current_tb = data["tiebreakers"].get(selected_player, 0)
                    tiebreaker = st.number_input(
                        "Tiebreaker: Total Goals scored in the Final (including extra time)", 
                        min_value=0, max_value=20, value=int(current_tb)
                    )
                    st.divider()
                
                for current_round in ROUND_ORDER:
                    round_matches = {m_id: m_info for m_id, m_info in active_matches.items() if m_info['round'] == current_round}
                    
                    if round_matches:
                        st.markdown(f"### 🏆 {current_round}")
                        st.divider()
                        
                        for match_id, match_info in round_matches.items():
                            kickoff_time = datetime.fromisoformat(match_info['kickoff_utc'].replace("Z", "+00:00"))
                            
                            if datetime.now(timezone.utc) < kickoff_time:
                                home_display = add_flag(match_info['team_home'])
                                away_display = add_flag(match_info['team_away'])
                                
                                options = ["Select Winner", home_display, away_display]
                                current_pick = data["picks"].get(selected_player, {}).get(match_id, "Select Winner")
                                
                                default_index = options.index(current_pick) if current_pick in options else 0
                                
                                choice = st.selectbox(
                                    f"{home_display} vs {away_display}", 
                                    options, 
                                    index=default_index,
                                    key=f"pick_{match_id}"
                                )
                                if choice != "Select Winner":
                                    new_picks[match_id] = choice
                            else:
                                st.warning(f"🔒 {add_flag(match_info['team_home'])} vs {add_flag(match_info['team_away'])} - Match locked.")
                        
                        st.write("") 
                        
                submitted = st.form_submit_button("Save Picks")
                if submitted:
                    data["picks"][selected_player].update(new_picks)
                    if has_final_round:
                        data["tiebreakers"][selected_player] = tiebreaker
                    save_data(data)
                    st.success("Picks saved successfully! Changes are permanently backed up.")

# --- TAB 3: MANAGE POOL ---
with tab3:
    st.header("Pool Administration")
    
    input_password = st.text_input("Enter Admin Password:", type="password")
    master_password = st.secrets.get("ADMIN_PASSWORD", "admin_fallback_default")
    
    if input_password != master_password:
        st.warning("🔒 This section is restricted to the App Owner. Enter the admin password to unlock management tools.")
    else:
        st.success("Admin permissions unlocked.")
        st.subheader("Manage Players")
        
        players_text = "\n".join(PLAYERS)
        updated_text = st.text_area("Enter player names (One name per line):", value=players_text)
        
        if st.button("Save Player List"):
            new_player_list = [name.strip() for name in updated_text.split("\n") if name.strip()]
            
            updated_picks = {}
            updated_tiebreakers = {}
            for player in new_player_list:
                updated_picks[player] = data["picks"].get(player, {})
                updated_tiebreakers[player] = data["tiebreakers"].get(player, 0)
                
            data["players"] = new_player_list
            data["picks"] = updated_picks
            data["tiebreakers"] = updated_tiebreakers
            
            save_data(data)
            st.success("Player database updated successfully!")
            st.rerun()
            
        st.divider()
        st.subheader("🔗 Generate Unique Player Links")
        st.write("Copy and send these custom web addresses to your players:")
        
        base_url = st.secrets.get("APP_URL", "https://your-app-name.streamlit.app").rstrip("/")
        
        for player in PLAYERS:
            encoded_name = urllib.parse.quote_plus(player)
            player_link = f"{base_url}/?player={encoded_name}"
            st.text_input(f"Link for {player}:", value=player_link, key=f"link_{player}")
