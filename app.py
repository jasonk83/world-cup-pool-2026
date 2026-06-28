import streamlit as st
import json
import os
from datetime import datetime, timezone
import urllib.parse

# --- CONFIGURATION ---
DATA_FILE = "data.json"
POINTS_MAP = {
    "Round of 32": 3,
    "Round of 16": 6,
    "Quarter-finals": 9,
    "Semi-finals": 12,
    "Final": 15
}

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
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
PLAYERS = data["players"]

st.title("🏆 2026 World Cup Pool")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["Dashboard & Standings", "Submit Picks", "Manage Pool"])

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
    
    visible_matches = {
        m_id: m_info for m_id, m_info in data["matches"].items() 
        if m_info['team_home'] != "TBD" and m_info['team_away'] != "TBD"
    }
    
    if not visible_matches:
        st.info("Waiting for upcoming round matchups to be determined.")
    else:
        for match_id, match_info in visible_matches.items():
            st.subheader(f"{match_info['team_home']} vs {match_info['team_away']}")
            st.caption(f"Round: {match_info['round']} | Kickoff: {match_info['kickoff_utc']} UTC")
            
            kickoff_time = datetime.fromisoformat(match_info['kickoff_utc'].replace("Z", "+00:00"))
            is_live_or_past = now_utc >= kickoff_time
            
            cols = st.columns(len(PLAYERS) if len(PLAYERS) > 0 else 1)
            for idx, player in enumerate(PLAYERS):
                with cols[idx]:
                    pick = data["picks"].get(player, {}).get(match_id, "No Pick")
                    if not is_live_or_past and pick != "No Pick":
                        st.write(f"**{player}**: 🔒 [Hidden]")
                    else:
                        if match_info["status"] == "Match Finished" and pick == match_info["winner"]:
                            st.success(f"**{player}**: {pick}")
                        elif match_info["status"] == "Match Finished" and pick != match_info["winner"] and pick != "No Pick":
                            st.error(f"**{player}**: {pick}")
                        else:
                            st.write(f"**{player}**: {pick}")

# --- TAB 2: SUBMIT PICKS (WITH LINK LOCKING) ---
with tab2:
    st.header("Submit Your Picks")
    
    # Read the ?player= parameter from the website URL link
    url_player = st.query_params.get("player", None)
    
    if not url_player or url_player not in PLAYERS:
        st.error("⚠️ **Access Denied:** You must use your unique personal link to submit picks. This prevents players from modifying entries belonging to competitors.")
        st.info("Please request your personalized submission link from the pool administrator.")
    else:
        st.success(f"Verified Entry Session For: **{url_player}**")
        
        # Display the selectbox but lock it completely so it cannot be toggled
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
                
                for match_id, match_info in active_matches.items():
                    kickoff_time = datetime.fromisoformat(match_info['kickoff_utc'].replace("Z", "+00:00"))
                    
                    if datetime.now(timezone.utc) < kickoff_time:
                        options = ["Select Winner", match_info['team_home'], match_info['team_away']]
                        current_pick = data["picks"].get(selected_player, {}).get(match_id, "Select Winner")
                        
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
                    if has_final_round:
                        data["tiebreakers"][selected_player] = tiebreaker
                    save_data(data)
                    st.success("Picks saved successfully!")

# --- TAB 3: MANAGE POOL (PASSWORD PROTECTED) ---
with tab3:
    st.header("Pool Administration")
    
    # Prompt for secret password configured in Phase 1
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
        st.write("Copy and send these custom web addresses to your players. These links automatically log them in and block access to other players' ballots.")
        
        base_url = st.secrets.get("APP_URL", "https://your-app-name.streamlit.app").rstrip("/")
        
        for player in PLAYERS:
            encoded_name = urllib.parse.quote_plus(player)
            player_link = f"{base_url}/?player={encoded_name}"
            st.text_input(f"Link for {player}:", value=player_link, key=f"link_{player}")
