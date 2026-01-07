from flask import Flask, request, render_template
from collections import defaultdict
import pandas as pd
import io

app = Flask(__name__)

# -------------------------------
# Helper Functions
# -------------------------------

def safe_int(value):
    try:
        return int(float(value))
    except:
        return 0

def safe_float(value):
    try:
        return float(value)
    except:
        return 0

def parse_csv(file):
    """Parse the uploaded CSV or XLSX without needing a SECTION column"""
    my_hitters = []
    my_pitchers = []
    opp_hitters = []
    opp_pitchers = []

    try:
        if file.filename.endswith(".xlsx"):
            xls = pd.ExcelFile(file)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                section = sheet.strip().upper()
                if "MY_HITTER" in section:
                    my_hitters = df.to_dict(orient="records")
                elif "MY_PITCHER" in section:
                    my_pitchers = df.to_dict(orient="records")
                elif "OPP_HITTER" in section:
                    opp_hitters = df.to_dict(orient="records")
                elif "OPP_PITCHER" in section:
                    opp_pitchers = df.to_dict(orient="records")
        else:
            # Single CSV file: assume columns contain a "Type" column
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                t = str(row.get("Type", "")).strip().upper()
                if t == "MY_HITTER":
                    my_hitters.append(row.to_dict())
                elif t == "MY_PITCHER":
                    my_pitchers.append(row.to_dict())
                elif t == "OPP_HITTER":
                    opp_hitters.append(row.to_dict())
                elif t == "OPP_PITCHER":
                    opp_pitchers.append(row.to_dict())

    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")

    return my_hitters, my_pitchers, opp_hitters, opp_pitchers

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

@app.route("/", methods=["GET", "POST"])
def index():
    lineup = None
    rotation = None
    error = None

    if request.method == "POST":
        try:
            if "stats_file" not in request.files:
                raise ValueError("No file uploaded.")

            file = request.files["stats_file"]
            if file.filename == "":
                raise ValueError("No file selected.")

            # Parse the uploaded file
            my_hitters, my_pitchers, opp_hitters, opp_pitchers = parse_csv(file)

            if not my_hitters:
                raise ValueError("No valid hitter stats found for your team.")
            if not my_pitchers:
                raise ValueError("No valid pitcher stats found for your team.")
            if not opp_pitchers:
                raise ValueError("No valid opponent pitcher stats found.")

            lineup = build_lineup(my_hitters, opp_pitchers)
            rotation = sorted(my_pitchers, key=lambda p: safe_float(p.get("ERA", 99)))[:3]

        except Exception as e:
            error = f"Error processing file: {str(e)}"

    return render_template("index.html", lineup=lineup, rotation=rotation, error=error)

# -------------------------------
# Run Flask
# -------------------------------

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
