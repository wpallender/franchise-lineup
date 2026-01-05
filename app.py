from flask import Flask, request, render_template
from collections import defaultdict

app = Flask(__name__)

# -------------------------------
# Helper Functions
# -------------------------------

def parse_stats(text):
    """Parse pasted TSV stats into a list of dictionaries. Skip malformed lines."""
    lines = [l for l in text.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return []

    headers = [h.strip() for h in lines[0].split("\t")]
    players = []

    for line in lines[1:]:
        values = [v.strip() for v in line.split("\t")]
        if len(values) != len(headers):
            continue  # skip malformed rows
        player = {headers[i]: values[i] for i in range(len(headers))}
        players.append(player)

    return players

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

def score_player(player, opp_pitcher=None):
    """Simple hitter scoring formula: Avg, HR, RBI, OBP"""
    avg = safe_float(player.get("Avg", 0))
    hr = safe_int(player.get("HR", 0))
    rbi = safe_int(player.get("RBI", 0))
    obp = safe_float(player.get("OBP", 0))

    score = avg * 100 + hr * 5 + rbi * 2 + obp * 100
    return score

def build_lineup(my_hitters, opp_pitchers):
    """Build lineup by selecting best hitter per position"""
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
            my_hitters_text = request.form.get("my_hitters", "")
            my_pitchers_text = request.form.get("my_pitchers", "")
            opp_hitters_text = request.form.get("opp_hitters", "")
            opp_pitchers_text = request.form.get("opp_pitchers", "")

            my_hitters = parse_stats(my_hitters_text)
            my_pitchers = parse_stats(my_pitchers_text)
            opp_hitters = parse_stats(opp_hitters_text)
            opp_pitchers = parse_stats(opp_pitchers_text)

            if not my_hitters:
                raise ValueError("No valid hitter stats found for your team.")
            if not my_pitchers:
                raise ValueError("No valid pitcher stats found for your team.")
            if not opp_pitchers:
                raise ValueError("No valid opponent pitcher stats found.")

            lineup = build_lineup(my_hitters, opp_pitchers)

            # Build top 3 rotation by lowest ERA
            rotation = sorted(my_pitchers, key=lambda p: safe_float(p.get("ERA", 99)))[:3]

        except Exception as e:
            error = f"Error processing stats: {str(e)}"

    return render_template(
        "index.html",
        lineup=lineup,
        rotation=rotation,
        error=error,
        form_data=request.form
    )

# -------------------------------
# Run Flask
# -------------------------------

import os

if __name__ == "__main__":
    # Use Render's PORT if available, otherwise default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)







