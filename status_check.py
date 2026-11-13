"""Daily app status check. Writes report.md only when something is wrong."""
import json
import urllib.request

# "sp"   = Atlassian Statuspage feed at <base>/api/v2/status.json
# "http" = page just has to answer without an error
APPS = [
    ("Procore", "sp", "https://status.procore.com"),
    ("monday.com", "sp", "https://status.monday.com"),
    ("Nearmap", "sp", "https://status.nearmap.com"),
    ("Vanta", "sp", "https://status.vanta.com"),
    ("Autodesk", "http", "https://health.autodesk.com"),
    # Add more as you confirm their status pages, e.g.:
    # ("Sine", "sp", "https://status.sine.co"),
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "app-status-check"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


problems = []
for name, kind, base in APPS:
    try:
        if kind == "sp":
            status = json.loads(fetch(base + "/api/v2/status.json"))["status"]
            if status["indicator"] != "none":
                problems.append(f"- **{name}**: {status['description']} ({base})")
        else:
            fetch(base)
    except Exception as e:
        problems.append(f"- **{name}**: check failed, {type(e).__name__} ({base})")

if problems:
    with open("report.md", "w") as f:
        f.write("\n".join(problems) + "\n")
print("\n".join(problems) or "All apps operational")
