# 🏆 2026 World Cup Pool Coordinator

A fully automated, serverless tournament pool application built with Python and Streamlit. 

This application manages a round-by-round prediction pool for the knockout stages (Round of 32 through the Final) of the 2026 FIFA World Cup. It uses GitHub Actions to fetch live scores automatically and uses the GitHub API to permanently store player picks, completely circumventing Streamlit's ephemeral container storage.

## ✨ Features

* **Live Automated Scoring:** A daily GitHub Actions cron job pings the [Football-Data.org](https://www.football-data.org/) API to update match matchups, kickoff times, and live winners.
* **Persistent Storage:** Player picks and standings are saved to a local `data.json` file and automatically pushed back to the GitHub repository via the GitHub API whenever a user submits their picks.
* **Anti-Tampering URLs:** Players receive unique entry links (e.g., `/?player=Name`). The app reads the URL parameter, locks the dropdown selection to that specific user, and prevents competitors from modifying each other's picks.
* **Admin Dashboard:** A password-protected management tab allows the pool host to easily add/remove players and generate secure invite links.
* **Smart UI:** Matchups remain hidden as "TBD" until lower rounds conclude. Competitor picks remain fully masked as `🔒 [Hidden]` until the exact kickoff time passes.
* **Dynamic Timezones & Flags:** Kickoff times automatically display in ET and CT, with dynamically mapped country flag emojis for an elevated visual experience.

---

## 📈 Scoring System (The Doubling Method)

To keep the pool highly competitive until the final whistle, the app uses a doubling scoring system. This perfectly offsets the halving of available matches each round, ensuring exactly 32 points are available in every stage.

| Tournament Round | Matchups | Points Per Pick | Total Points Available |
| :--- | :---: | :---: | :---: |
| **Round of 32** | 16 | 2 | 32 |
| **Round of 16** | 8 | 4 | 32 |
| **Quarter-finals** | 4 | 8 | 32 |
| **Semi-finals** | 2 | 16 | 32 |
| **Final** | 1 | 32 | 32 |

*Tiebreaker: Total goals scored in the Final match (including extra time).*

---

## 🚀 How to Fork & Deploy Your Own Pool

### Phase 1: Fork and Configure the Backend
1. **Fork** this repository to your own GitHub account.
2. Go to **Settings > Actions > General** in your new repository. Scroll down to **Workflow permissions** and ensure **Read and write permissions** is selected. Click Save.
3. Get a free API key from [Football-Data.org](https://www.football-data.org/).
4. In your GitHub repository, go to **Settings > Secrets and variables > Actions**. 
5. Add a new repository secret named `API_FOOTBALL_KEY` and paste your API key as the value.
6. Go to the **Actions** tab in GitHub, select the **Update World Cup Scores** workflow, and click **Run workflow** to generate your initial `data.json` file.

### Phase 2: Generate a GitHub Token for Persistent Storage
Because Streamlit Cloud resets periodically, the app needs permission to push player picks back to your repository.
1. Go to your personal GitHub settings: **Settings > Developer settings > Personal access tokens > Fine-grained tokens**.
2. Generate a new token restricted *only* to your forked repository.
3. Under **Repository permissions**, grant **Read and write** access for **Contents**.
4. Generate and copy the token (`github_pat_...`).

### Phase 3: Deploy to Streamlit
1. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and click **New app**.
2. Connect your forked GitHub repository and select `app.py` as the main file path. Click **Deploy**.
3. Once deployed, click the three dots (**`⋮`**) in the top right corner of your app and select **Settings > Secrets**.
4. Paste the following configuration block, updating it with your specific details:

```toml
# Your custom admin password to unlock the Manage Pool tab
ADMIN_PASSWORD = "YourSuperSecretPasswordHere"

# The public URL of your deployed Streamlit app
APP_URL = "[https://your-app-name.streamlit.app](https://your-app-name.streamlit.app)"

# Your fine-grained GitHub Personal Access Token (from Phase 2)
GITHUB_TOKEN = "github_pat_xxxxxxxxx"

# Your GitHub Username and Repository Name
GITHUB_REPO = "YourUsername/Your-Repo-Name"
