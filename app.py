import streamlit as st
import json
import os
from datetime import datetime, timezone

# --- CONFIGURATION ---
DATA_FILE = "data.json"
PLAYERS = ["Player 1", "Player 2", "Player 3", "Player 4"]
POINTS_MAP = {
    "Round of 32": 3,
    "Round of 16": 6,
    "Quarter-finals": 9,
    "Semi-finals": 12,
    "Final": 15
}

# --- DATA LOADING ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"matches": {}, "picks": {p: {} for p in PLAYERS}, "tiebreakers": {p: 0 for p in PLAYERS}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

st.title("🏆 2026 World Cup Pool")

# --- TABS ---
tab1, tab2 = st.tabs(["Dashboard & Standings", "Submit Picks"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("Current Standings")
    
    # Calculate Scores
    scores = {p: 0 for p in PLAYERS}
    for match_id, match_info in data["matches"].items():
        if match_info["status"] == "Match Finished":
            winner = match_info["winner"]
            round_name = match_info["round"]
            points = POINTS_MAP.get(round_name, 0)
            
            for player in PLAYERS:
                if data["picks"].get(player, {}).get(match_id) == winner:
                    scores[player] += points

    # Display Leaderboard
    st.dataframe([{"Player": p, "Points": s} for p, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)])

    st.divider()
    st.header("Matchups & Picks")
    
    now_utc = datetime.now(timezone.utc)
    
    for match_id, match_info in data["matches"].items():
        st.subheader(f"{match_info['team_home']} vs {match_info['team_away']}")
        st.caption(f"Round: {match_info['round']} | Kickoff: {match_info['kickoff_utc']} UTC")
        
        # Strict UTC parsing to prevent offset bugs
        kickoff_time = datetime.fromisoformat(match_info['kickoff_utc'].replace("Z", "+00:00"))
        is_live_or_past = now_utc >= kickoff_time
        
        # Display picks
        cols = st.columns(4)
        for idx, player in enumerate(PLAYERS):
            with cols[idx]:
                pick = data["picks"].get(player, {}).get(match_id, "No Pick")
                if not is_live_or_past and pick != "No Pick":
                    st.write(f"**{player}**: 🔒 [Hidden]")
                else:
                    # Highlight if correct
                    if match_info["status"] == "Match Finished" and pick == match_info["winner"]:
                        st.success(f"**{player}**: {pick}")
                    elif match_info["status"] == "Match Finished" and pick != match_info["winner"] and pick != "No Pick":
                        st.error(f"**{player}**: {pick}")
                    else:
                        st.write(f"**{player}**: {pick}")

# --- TAB 2: SUBMIT PICKS ---
with tab2:
    st.header("Submit Your Picks")
    selected_player = st.selectbox("Who are you?", PLAYERS)
    
    with st.form("picks_form"):
        new_picks = {}
        tiebreaker = st.number_input("Tiebreaker: Total Goals in Final", min_value=0, max_value=20, value=0)
        
        for match_id, match_info in data["matches"].items():
            kickoff_time = datetime.fromisoformat(match_info['kickoff_utc'].replace("Z", "+00:00"))
            
            # Only allow picking if match hasn't started
            if datetime.now(timezone.utc) < kickoff_time:
                options = ["Select Winner", match_info['team_home'], match_info['team_away']]
                current_pick = data["picks"].get(selected_player, {}).get(match_id, "Select Winner")
                
                # Ensure the current pick is in the options, otherwise default to "Select Winner"
                default_index = options.index(current_pick) if current_pick in options else 0
                
                choice = st.selectbox(
                    f"{match_info['team_home']} vs {match_info['team_away']} ({match_info['round']})", 
                    options, 
                    index=default_index,
                    key=f"pick_{match_id}"
                )
                if choice != "Select Winner":
                    new_picks[match_id] = choice
            else:
                st.warning(f"🔒 {match_info['team_home']} vs {match_info['team_away']} - Match locked.")
                
        submitted = st.form_submit_button("Save Picks")
        if submitted:
            data["picks"][selected_player].update(new_picks)
            data["tiebreakers"][selected_player] = tiebreaker
            save_data(data)
            st.success("Picks saved successfully!")
