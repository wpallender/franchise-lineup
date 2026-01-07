from flask import Flask, request, render_template
from collections import defaultdict
import csv
import io

app = Flask(__name__)

# -------------------------------
# Helpers
# -------------------------------

def safe_int(v):
    try:
        return int(float(v))
    except:
        return 0

def safe_float(v):
    try:
        return float(v)
    except:
        return 0

def parse_csv(file):
    my_hitters = []
    my_pitchers = []
    opp_hitters = []
    opp_pitchers = []

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    for row in reader:
        row_type = row.get("Type", "").strip().upper()
        if not row_type:
            continue

        if row_type == "MY_HITTER":
            my_hitters.append(row)
        elif row_type == "MY_PITCHER":
            my_pitchers.append(row)
        elif row_type == "OPP_HITTER":
            opp_hitters.append(row)
        elif row_type == "OPP_PITCHER":
            opp_pitchers.append(row)

    return my_hitters, my_pitchers, opp_hitters, opp_pitchers

def score_player(player, opp_pitcher=None):
    avg = safe_float(player.get("Avg"))
    hr = safe_int(player.get("HR"))
    rbi = safe_int(player.get("RBI"))
    obp = safe_float(player.get("OBP"))

    return avg * 100 + hr * 5 + rbi * 2 + obp * 100

def build_lineup(my_hitters, opp_pitchers):
    by_pos = defaultdict(list)

    for p in my_hitters:
        pos = p.get("POS", "").strip()
        if pos:
            by_pos[pos].append(p)

    lineup = []
    for pos, players in by_pos.items():
        best = max(players, key=score_player)
        best["Score"] = round(score_player(best), 1)
        lineup.append(best)

    return lineup

# -------------------------------
# Route
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

            my_hitters, my_pitchers, opp_hitters, opp_pitchers = parse_csv(file)

            if not my_hitters:
                raise ValueError("No MY_HITTER rows found.")
            if not my_pitchers:
                raise ValueError("No MY_PITCHER rows found.")
            if not opp_pitchers:
                raise ValueError("No OPP_PITCHER rows found.")

            lineup = build_lineup(my_hitters, opp_pitchers)
            rotation = sorted(
                my_pitchers,
                key=lambda p: safe_float(p.get("ERA", 99))
            )[:3]

        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        lineup=lineup,
        rotation=rotation,
        error=error
    )

# -------------------------------
# Run
# -------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
