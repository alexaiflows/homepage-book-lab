# main.py — 시트로 페이지를 만들고 저장해 둔 판을 남긴다(8장)
import csv
import io
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.request import urlopen

from holidays import holiday_line

ROOT = Path(__file__).parent
SITE = ROOT / "_site"
SKIP = {"main.py", "holidays.py", "template.html", "data", "README.md"}
KST = timezone(timedelta(hours=9))  # 한국 시각
COLUMNS = ["제목", "설명", "분류", "링크", "상태", "공개"]

def skip(folder, names):  # 점(.)이나 밑줄(_)로 시작하는 것도 뺀다
    return [n for n in names if n.startswith((".", "_")) or n in SKIP]

def fetch(url):
    with urlopen(url, timeout=20) as res:
        return res.read().decode("utf-8-sig")

def load_sheet():  # 시트를 못 읽거나 열 이름이 없으면 예외
    url = os.environ.get("SHEET_CSV_URL", "")
    if not url:
        raise ValueError("SHEET_CSV_URL이 없습니다")
    text = fetch(url)
    if text.lstrip().startswith("<"):
        raise ValueError("CSV 대신 웹페이지가 왔습니다")
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"열 이름이 없습니다: {', '.join(missing)}")
    return list(reader)

def check_rows(rows):  # 잘못된 행은 빼고 로그에 남긴다
    good = []
    for n, row in enumerate(rows, start=2):  # 1행은 열 이름
        show = (row["공개"] or "").strip()
        if show not in ("Y", "N"):
            print(f"경고: {n}행 공개 값 {show!r}가 Y나 N이 아니라 뺍니다")
        elif show == "Y" and not (row["제목"] or "").strip():
            print(f"경고: {n}행 제목이 비어 뺍니다")
        elif show == "Y":
            if row["링크"] and not row["링크"].startswith("http"):
                print(f"경고: {n}행 링크 형식이 달라 링크만 뺍니다")
                row["링크"] = ""
            good.append(row)
    return good

def load_projects(now):  # 시트를 못 읽으면 저장해 둔 판으로
    try:
        rows, note = check_rows(load_sheet()), ""
        saved = {"수집 시각": f"{now:%Y-%m-%d %H:%M}", "프로젝트": rows}
    except Exception as error:
        print(f"경고: 시트를 못 읽었습니다 — {error}")
        url = os.environ.get("SITE_URL", "") + "/data/projects.json"
        try:
            saved = json.loads(fetch(url))
        except Exception:  # 멈추면 게시하지 않아 이전 공개본이 남는다
            raise SystemExit("저장해 둔 판도 없어 멈춥니다")
        rows, when = saved["프로젝트"], saved["수집 시각"]
        note = f'<p class="intro-text">저장해 둔 판(마지막 수집 {when})</p>'
    (SITE / "data").mkdir(exist_ok=True)
    text = json.dumps(saved, ensure_ascii=False, indent=1)
    (SITE / "data" / "projects.json").write_text(text, encoding="utf-8")
    return rows, note

def grouped(rows):  # 분류마다 이름표 한 줄과 카드들
    parts = []
    for kind in sorted({row["분류"] for row in rows}):
        cards = "\n      ".join(card(r) for r in rows if r["분류"] == kind)
        label = f'<p class="eyebrow">{escape(kind)}</p>'
        parts.append(f"{label}\n      {cards}")
    return "\n      ".join(parts)

def card(row):
    title = escape(row["제목"])
    if row["링크"]:
        title = f'<a href="{escape(row["링크"])}">{title}</a>'
    return f"""<article class="project-card">
        <span class="status">{escape(row["상태"])}</span>
        <h3>{title}</h3>
        <p>{escape(row["설명"])}</p>
      </article>"""

def holiday(now):  # 공휴일은 덧붙이는 정보라 실패해도 그 줄만 뺀다
    try:
        return holiday_line(now)
    except SystemExit as error:
        print(f"경고: {error}")
        return ""

def build_page(rows, note, now):
    page = (ROOT / "template.html").read_text(encoding="utf-8")
    if rows:
        pick = card(rows[now.toordinal() % len(rows)])  # 날마다 바뀜
    else:  # 빈 자료 — 안내 문장
        pick = "<p>지금 보여 줄 프로젝트가 없습니다. 곧 채우겠습니다.</p>"
    page = page.replace("{알림}", note).replace("{추천}", pick)
    page = page.replace("{목록}", grouped(rows))
    page = page.replace("{공휴일}", holiday(now))
    page = page.replace("{개수}", str(len(rows)))
    return page.replace("{생성 시각}", f"{now:%Y-%m-%d %H:%M}")

shutil.rmtree(SITE, ignore_errors=True)
shutil.copytree(ROOT, SITE, ignore=skip)
now = datetime.now(KST)
rows, note = load_projects(now)
page = build_page(rows, note, now)
(SITE / "projects.html").write_text(page, encoding="utf-8")
print(f"projects.html: 공개 {len(rows)}개, 생성 {now:%Y-%m-%d %H:%M}")
