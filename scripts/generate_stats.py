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

from html import escape
P='#ff4fa3'; C='#3ef3ff'; BG='#0b0b12'; DIM='#6b6f80'; TXT='#e9e9f2'
F="font-family=\"'JetBrains Mono',Consolas,monospace\""
def window(title, body, h):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="{h}" viewBox="0 0 500 {h}">
<style>.cur{{animation:b 1s steps(1) infinite}}@keyframes b{{50%{{opacity:0}}}}
.grow{{animation:g 1.6s ease-out both}}@keyframes g{{from{{transform:scaleX(0)}}}}
.row{{animation:r .4s ease-out both}}@keyframes r{{from{{opacity:0;transform:translateX(-8px)}}}}</style>
<rect x="1" y="1" width="498" height="{h-2}" rx="8" fill="{BG}" stroke="{P}" stroke-opacity=".55"/>
<path d="M1 30 H499" stroke="{P}" stroke-opacity=".35"/>
<circle cx="18" cy="16" r="4.5" fill="{P}"/><circle cx="34" cy="16" r="4.5" fill="{C}" opacity=".8"/><circle cx="50" cy="16" r="4.5" fill="{DIM}"/>
<text x="250" y="20" text-anchor="middle" {F} font-size="11" fill="{DIM}">{escape(title)}</text>
<g {F}>{body}</g></svg>'''
def stats_card(rows, prompt):
    body=f'<text x="20" y="56" font-size="13" fill="{P}">sangfuu@nightcity<tspan fill="{DIM}">:~$</tspan> <tspan fill="{TXT}">{escape(prompt)}</tspan></text>'
    for i,(k,v) in enumerate(rows):
        y=88+i*26; d=f'style="animation-delay:{.15*i:.2f}s"'
        dots='.'*(34-len(k)-len(str(v)))
        body+=f'<g {d}><text x="20" y="{y}" font-size="13" fill="{C}">›</text><text x="36" y="{y}" font-size="13" fill="{TXT}">{escape(k)}<tspan fill="{DIM}"> {dots} </tspan><tspan fill="{P}" font-weight="700">{v}</tspan></text></g>'
    y=88+len(rows)*26
    body+=f'<text x="20" y="{y+6}" font-size="13" fill="{P}">sangfuu@nightcity<tspan fill="{DIM}">:~$</tspan></text><rect class="cur" x="178" y="{y-6}" width="8" height="14" fill="{P}"/>'
    return window('git-stats — bash — 80×24', body, y+28)
def langs_card(langs, prompt):
    body=f'<text x="20" y="56" font-size="13" fill="{P}">sangfuu@nightcity<tspan fill="{DIM}">:~$</tspan> <tspan fill="{TXT}">{escape(prompt)}</tspan></text>'
    for i,(name,pct) in enumerate(langs):
        y=88+i*26; w=200*pct/100
        body+=f'<g style="animation-delay:{.15*i:.2f}s"><text x="20" y="{y}" font-size="13" fill="{TXT}">{escape(name)}</text>'
        body+=f'<rect x="120" y="{y-10}" width="200" height="11" fill="#1a1a26"/>'
        body+=f'<rect x="120" y="{y-10}" width="{w:.1f}" height="11" fill="{P if i%2==0 else C}"/>'
        body+=''.join(f'<rect x="{120+k}" y="{y-10}" width="1" height="11" fill="{BG}"/>' for k in range(10,200,10))
        body+=f'<text x="336" y="{y}" font-size="13" fill="{DIM}">{pct:5.1f}%</text></g>'
    y=88+len(langs)*26
    body+=f'<text x="20" y="{y+6}" font-size="13" fill="{P}">sangfuu@nightcity<tspan fill="{DIM}">:~$</tspan></text><rect class="cur" x="178" y="{y-6}" width="8" height="14" fill="{P}"/>'
    return window('langs — bash — 80×24', body, y+28)

c = user["contributionsCollection"]
rows = [
 ("commits.last_year", c["totalCommitContributions"]),
 ("pull_requests", c["totalPullRequestContributions"]),
 ("issues", c["totalIssueContributions"]),
 ("repos.contributed", c["totalRepositoryContributions"]),
 ("public_stars", stars)]
total = sum(languages.values())
langs = [(name, amount / total * 100) for name, amount in languages.most_common(5)] if total else []
out = Path("assets")
out.mkdir(exist_ok=True)
(out / "github-stats.svg").write_text(stats_card(rows, "git stats --year"), encoding="utf-8")
(out / "top-langs.svg").write_text(langs_card(langs, "langs --top 5"), encoding="utf-8")
