# C01 | main.py — 사이트를 _site에 모으고 projects.html을 만든다
import json
import shutil
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "_site"
SKIP = {"main.py", "data", "README.md"}  # 공개 사이트에 넣지 않는 것
KST = timezone(timedelta(hours=9))  # 한국 시각

def skip(folder, names):  # 점(.)이나 밑줄(_)로 시작하는 것도 뺀다
    return [n for n in names if n.startswith((".", "_")) or n in SKIP]

def load_projects():
    text = (ROOT / "data" / "projects.json").read_text(encoding="utf-8")
    return [row for row in json.loads(text) if row["공개"] == "Y"]

def card(row):
    title = escape(row["제목"])
    if row["링크"]:
        title = f'<a href="{escape(row["링크"])}">{title}</a>'
    return f"""<article class="project-card">
        <span class="status">{escape(row["상태"])}</span>
        <h3>{title}</h3>
        <p>{escape(row["설명"])} ({escape(row["분류"])})</p>
      </article>"""

def build_page(rows, now):
    pick = rows[now.toordinal() % len(rows)]  # 날마다 바뀌는 추천
    cards = "\n      ".join(card(row) for row in rows)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>프로젝트 목록</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="container">
    <p class="intro"><a href="index.html">첫 화면으로</a></p>
    <h1>프로젝트 목록</h1>
    <section class="section">
      <h2>오늘의 추천</h2>
      {card(pick)}
    </section>
    <section class="section">
      <h2>전체 {len(rows)}개</h2>
      {cards}
    </section>
  </main>
  <footer class="site-footer container">
    <p>생성 시각: {now:%Y-%m-%d %H:%M} (한국 시각)</p>
  </footer>
</body>
</html>
"""

shutil.rmtree(SITE, ignore_errors=True)
shutil.copytree(ROOT, SITE, ignore=skip)
rows = load_projects()
now = datetime.now(KST)
page = build_page(rows, now)
(SITE / "projects.html").write_text(page, encoding="utf-8")
print(f"projects.html: 공개 {len(rows)}개, 생성 {now:%Y-%m-%d %H:%M}")
