"""Daily app status check. Writes report.md only when something is wrong."""
import json
import time
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


def fetch(url, attempts=3):
    req = urllib.request.Request(url, headers={"User-Agent": "app-status-check"})
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(10 * (i + 1))  # slow feeds often answer on a retry


def details(base):
    """Affected components and open incidents, from the Statuspage summary."""
    try:
        s = json.loads(fetch(base + "/api/v2/summary.json"))
    except Exception:
        return ["    - (details unavailable)"]
    lines = [f"    - Incident: {i['name']} ({i['impact']}, {i['status']})"
             for i in s.get("incidents", [])]
    comps = s.get("components", [])
    groups = {c["id"]: c["name"] for c in comps if c.get("group")}
    for c in comps:
        if c["status"] != "operational" and not c.get("group"):
            where = groups.get(c.get("group_id"))
            label = f"{where} / {c['name']}" if where else c["name"]
            lines.append(f"    - {label}: {c['status'].replace('_', ' ')}")
    return lines


problems = []
for name, kind, base in APPS:
    try:
        if kind == "sp":
            status = json.loads(fetch(base + "/api/v2/status.json"))["status"]
            if status["indicator"] != "none":
                problems.append(f"- **{name}**: {status['description']} ({base})")
                problems.extend(details(base))
        else:
            fetch(base)
    except Exception as e:
        problems.append(f"- **{name}**: check failed, {type(e).__name__} ({base})")

if problems:
    with open("report.md", "w") as f:
        f.write("@jwilkinson879-alt\n\n" + "\n".join(problems) + "\n")
print("\n".join(problems) or "All apps operational")
