import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

login = os.environ["GITHUB_REPOSITORY"].split("/")[0]
query = """query($login:String!,$cursor:String) {
 user(login:$login) {
  contributionsCollection {
   totalCommitContributions totalPullRequestContributions
   totalIssueContributions totalRepositoryContributions
  }
  repositories(first:100,after:$cursor,ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false) {
   pageInfo { hasNextPage endCursor }
   nodes { stargazerCount languages(first:100,orderBy:{field:SIZE,direction:DESC}) { edges { size node { name color } } } }
  }
 }
}"""
languages = Counter()
colors = {}
stars = 0
cursor = None
while True:
    body = json.dumps({"query": query, "variables": {"login": login, "cursor": cursor}}).encode()
    req = Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Content-Type": "application/json", "User-Agent": "profile-stats"})
    with urlopen(req, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    user = result["data"]["user"]
    for repo in user["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            languages[name] += edge["size"]
            colors[name] = edge["node"]["color"] or "#FFA500"
    page = user["repositories"]["pageInfo"]
    if not page["hasNextPage"]:
        break
    cursor = page["endCursor"]

def text(x, y, value, color="#94a3b8", size=14, weight="normal"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(str(value))}</text>'

def card(title, content):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="250" viewBox="0 0 500 250" role="img" aria-label="' + escape(title, quote=True) + '"><rect x="1" y="1" width="498" height="248" rx="14" fill="#0f172a" stroke="#334155"/><g font-family="Segoe UI,Arial,sans-serif">' + text(24,36,title,"#FFA500",20,"bold") + content + '</g></svg>'

c = user["contributionsCollection"]
rows = [
 ("Commits", c["totalCommitContributions"]),
 ("Pull requests", c["totalPullRequestContributions"]),
 ("Issues", c["totalIssueContributions"]),
 ("Repositories contributed to", c["totalRepositoryContributions"]),
 ("Public repository stars", stars)]
content = ""
for i, (label, value) in enumerate(rows):
    y = 75 + i * 29
    content += text(24,y,label) + text(395,y,f"{value:,}","#ffffff",16,"bold")
year = datetime.now(timezone.utc).year
content += text(24,232,"Last 12 months · stars: public total",size=11)
out = Path("assets")
out.mkdir(exist_ok=True)
(out / "github-stats.svg").write_text(card("My GitHub Activity",content),encoding="utf-8")
content = ""
total = sum(languages.values())
for i, (name, amount) in enumerate(languages.most_common(5)):
    y = 75 + i * 29
    pct = amount / total * 100
    color = colors[name]
    content += text(24,y,name,"#ffffff")
    content += f'<rect x="190" y="{y-10}" width="210" height="9" rx="4" fill="#1e293b"/><rect x="190" y="{y-10}" width="{210*pct/100:.1f}" height="9" rx="4" fill="{color}"/>'
    content += text(415,y,f"{pct:.1f}%",size=12)
if not total:
    content += text(24,100,"No language data available yet.")
content += text(24,232,"Share of code · public repositories excluding forks",size=11)
(out / "top-langs.svg").write_text(card("Repository Languages",content),encoding="utf-8")
