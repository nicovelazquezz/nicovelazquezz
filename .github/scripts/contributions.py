#!/usr/bin/env python3
"""Genera dist/contributions-{dark,light}.svg replicando el calendario nativo de GitHub."""
import datetime
import json
import os
import urllib.request

LOGIN = os.environ.get("GH_LOGIN", "nicovelazquezz")
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount contributionLevel weekday } }
      }
    }
  }
}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
data = json.load(urllib.request.urlopen(req))
cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
total = cal["totalContributions"]
weeks = cal["weeks"]

LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", text="#e6edf3", label="#7d8590",
                 levels=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", label="#57606a",
                  levels=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]),
}

CELL, GAP = 10, 3
PITCH = CELL + GAP
PAD = 16
LEFT = PAD + 28
TITLE_Y = PAD + 14
MONTHS_Y = TITLE_Y + 24
GRID_Y = MONTHS_Y + 10
N = len(weeks)
GRID_W = N * PITCH - GAP
LEGEND_Y = GRID_Y + 7 * PITCH + 12
W = LEFT + GRID_W + PAD
H = LEGEND_Y + CELL + PAD

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_labels():
    raw, prev = [], None
    for i, w in enumerate(weeks):
        d = datetime.date.fromisoformat(w["contributionDays"][0]["date"])
        if prev is None or d.month != prev:
            raw.append((i, MONTHS[d.month - 1]))
        prev = d.month
    # descarta etiquetas pegadas (columna inicial con mes partido)
    return [(i, m) for j, (i, m) in enumerate(raw)
            if j + 1 >= len(raw) or raw[j + 1][0] - i >= 3]


def render(theme):
    p = THEMES[theme]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Helvetica,Arial,sans-serif">',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="6" fill="{p["bg"]}" stroke="{p["border"]}"/>',
         f'<text x="{PAD}" y="{TITLE_Y}" font-size="15" font-weight="600" fill="{p["text"]}">'
         f'{total:,} contributions in the last year</text>']
    for i, m in month_labels():
        s.append(f'<text x="{LEFT + i * PITCH}" y="{MONTHS_Y}" font-size="11" fill="{p["label"]}">{m}</text>')
    for lbl, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        s.append(f'<text x="{PAD}" y="{GRID_Y + row * PITCH + CELL - 2}" font-size="11" fill="{p["label"]}">{lbl}</text>')
    for i, w in enumerate(weeks):
        for d in w["contributionDays"]:
            lv = LEVEL[d["contributionLevel"]]
            s.append(f'<rect x="{LEFT + i * PITCH}" y="{GRID_Y + d["weekday"] * PITCH}" width="{CELL}" '
                     f'height="{CELL}" rx="2" fill="{p["levels"][lv]}">'
                     f'<title>{d["date"]}: {d["contributionCount"]}</title></rect>')
    lx = W - PAD - 132
    s.append(f'<text x="{lx}" y="{LEGEND_Y + 9}" font-size="11" fill="{p["label"]}">Less</text>')
    for k, c in enumerate(p["levels"]):
        s.append(f'<rect x="{lx + 30 + k * PITCH}" y="{LEGEND_Y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>')
    s.append(f'<text x="{lx + 30 + 5 * PITCH + 4}" y="{LEGEND_Y + 9}" font-size="11" fill="{p["label"]}">More</text>')
    s.append('</svg>')
    return "".join(s)


os.makedirs("dist", exist_ok=True)
for theme in THEMES:
    with open(f"dist/contributions-{theme}.svg", "w") as f:
        f.write(render(theme))
print(f"total={total} weeks={N} size={W}x{H}")
