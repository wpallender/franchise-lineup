from flask import Flask, request, render_template
from collections import defaultdict

app = Flask(__name__)

# -------------------------------
# Helper Functions
# -------------------------------

def safe_int(value):
    try:
        return int(value)
    except:
        return 0

def safe_float(value):
    try:
        return float(value)
    except:
        return 0

def parse_table(form, prefix, cols, rows):
    """Convert the table input into a list of dicts"""
    players = []
    for i in range(rows):
        player = {}
        empty_row = True
        for col in cols:
            key = f"{prefix}_{col}_{i}"
            val = form.get(key, "").strip()
            if val != "":
                empty_row = False
            player[col] = val
        if not empty_row:
            players.append(player)
    return players

def score_player(player, opp_pitcher=None):
    avg = safe_float(player.get("Avg", 0))
    hr = safe_int(player.get("HR", 0))
    rbi = safe_int(player.get("RBI", 0))
    obp = safe_float(player.get("OBP", 0))
    score = avg * 100 + hr * 5 + rbi * 2 + obp * 100
    return score

def build_lineup(my_hitters, opp_pitchers):
    opp_pitcher = opp_pitchers[0] if opp_pitchers else {}
    by_pos = defaultdict(list)
    for p in my_hitters:
        if "POS" in p:
            by_pos[p["POS"]].append(p)

    lineup = []
    for pos, players in by_pos.items():
        best_player = max(players, key=lambda x: score_player(x, opp_pitcher))
        best_player["Score"] = round(score_player(best_player, opp_pitcher), 1)
        lineup.append(best_player)
    return lineup

# -------------------------------
# Flask Route
# -------------------------------

@app.route("/", methods=["GET","POST"])
def index():
    lineup = None
    rotation = None
    error = None
    form_data = request.form
    if request.method == "POST":
        try:
            my_hitters = parse_table(form_data, "my_hitters", ["POS","Player","Avg","AB","Hits","SLG","RBI","2B","3B","HR","SB","BB","OBP"], 12)
            my_pitchers = parse_table(form_data, "my_pitchers", ["Player","Win","Loss","Saves","ERA","WHIP","BAA","K","BB","Hits","Runs","IP"], 7)
            opp_hitters = parse_table(form_data, "opp_hitters", ["POS","Name","Avg","Hits","HR","RBI","OBP"], 9)
            opp_pitchers = parse_table(form_data, "opp_pitchers", ["Name","ERA","WHIP","K","BB"], 1)

            if not my_hitters:
                raise ValueError("No valid hitter stats found for your team.")
            if not my_pitchers:
                raise ValueError("No valid pitcher stats found for your team.")
            if not opp_pitchers:
                raise ValueError("No valid opponent pitcher stats found.")

            lineup = build_lineup(my_hitters, opp_pitchers)
            rotation = sorted(my_pitchers, key=lambda p: safe_float(p.get("ERA", 99)))[:3]

        except Exception as e:
            error = f"Error processing stats: {str(e)}"

    return render_template("index.html", lineup=lineup, rotation=rotation, error=error, form_data=form_data)

# -------------------------------
# Run Flask
# -------------------------------

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
