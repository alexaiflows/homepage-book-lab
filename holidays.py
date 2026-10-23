# C04 | holidays.py — 공공데이터 특일 정보로 이번 달 공휴일 한 줄을 만든다
import json
import os
from html import escape
from urllib.parse import unquote, urlencode
from urllib.request import urlopen

URL = ("https://apis.data.go.kr/B090041/openapi/service/"
       "SpcdeInfoService/getRestDeInfo")

def holiday_line(today):
    key = unquote(os.environ.get("DATA_GO_KR_KEY", "")).strip()
    if not key:  # Secrets에 넣기 전(7.5절)에는 공휴일 줄을 건너뛴다
        print("DATA_GO_KR_KEY가 없어 공휴일 줄을 건너뜁니다")
        return ""
    query = urlencode({"ServiceKey": key, "solYear": today.year,
                       "solMonth": f"{today.month:02d}", "_type": "json"})
    try:  # 요청 주소에 키가 들어 있어 주소는 로그에 찍지 않는다
        with urlopen(f"{URL}?{query}", timeout=20) as res:
            text = res.read().decode("utf-8")
    except Exception as error:  # 키 오류는 401·403과 까닭 글로 온다
        why = error.read().decode("utf-8") if hasattr(error, "read") else ""
        why = " ".join((why or str(error)).split())[:160]  # 한 줄로
        code = getattr(error, "code", type(error).__name__)
        raise SystemExit(f"특일 정보 실패: {code} {why}")
    items = json.loads(text)["response"]["body"]["items"] or {"item": []}
    days = items["item"]  # 여러 개면 목록, 하나면 묶음 하나로 온다
    days = days if isinstance(days, list) else [days]
    names = [f"{int(d['locdate']) % 100}일 {d['dateName']}" for d in days]
    print(f"특일 정보: 이번 달 공휴일 {len(names)}개")
    line = escape(", ".join(names) or "없음")
    return f'<p class="intro-text">이번 달 공휴일: {line}</p>'
