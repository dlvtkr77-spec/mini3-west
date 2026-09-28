# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path
# 상대 주소를 전체 주소로 바꾸기 위해 urljoin을 불러온다
from urllib.parse import urljoin
# 수집 시각을 기록하기 위해 datetime을 불러온다
from datetime import datetime
# 한국 시간대를 쓰기 위해 ZoneInfo를 불러온다
from zoneinfo import ZoneInfo
# 페이지 사이에 쉬기 위해 time을 불러온다
import time

# 웹 페이지 요청용 requests를 불러온다
import requests
# HTML 해석용 BeautifulSoup을 불러온다
from bs4 import BeautifulSoup
# 표를 만들고 CSV로 저장하기 위해 pandas를 불러온다
import pandas as pd

# 페이지 주소 꼴 (page_num 자리에 페이지 번호를 넣는다)
PAGE_URL = "https://www.scrapethissite.com/pages/forms/?page_num={}"
# 최대 몇 페이지까지 수집할지 정한다
MAX_PAGES = 3
# 합계 몇 행 이상이면 멈출지 정한다
MIN_TOTAL_ROWS = 50
# 스크립트 파일 위치 기준 ../data/raw.csv 경로를 만든다
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw.csv"
# 저장할 열 이름과 순서를 정한다 (01_collect_p1.py와 같다)
COLUMNS = ["name", "year_raw", "wins_raw", "detail_url", "scraped_at", "goals_for_raw"]


# 칸 하나의 글자를 앞뒤 공백만 정리해서 돌려주는 함수
def cell_text(row, css_class):
    # 해당 클래스를 가진 td 칸을 찾는다
    td = row.select_one(f"td.{css_class}")
    # 칸이 없으면 빈 글자를 돌려준다
    if td is None:
        return ""
    # 칸의 글자를 꺼내 앞뒤 공백만 지운다 (숫자로 바꾸지 않는다)
    return td.get_text().strip()


# 응답에 맞는 인코딩을 정하는 함수
def pick_encoding(response):
    # 응답 헤더 Content-Type에 charset이 있으면 그것을 쓴다
    content_type = response.headers.get("Content-Type", "")
    # charset= 뒤의 값을 찾는다
    if "charset=" in content_type.lower():
        # charset= 뒤 글자를 잘라 인코딩 이름으로 쓴다
        return content_type.lower().split("charset=")[-1].split(";")[0].strip()
    # 헤더에 없으면 HTML 안의 meta charset을 찾아본다
    meta = BeautifulSoup(response.content, "html.parser").select_one("meta[charset]")
    # meta charset이 있으면 그것을 쓴다
    if meta is not None and meta.get("charset"):
        return meta["charset"].strip()
    # 둘 다 모르면 utf-8을 쓴다
    return "utf-8"


# 한 페이지의 HTML에서 행 목록을 뽑는 함수
def parse_rows(html, page_url, scraped_at):
    # 응답 글자를 BeautifulSoup으로 해석한다
    soup = BeautifulSoup(html, "html.parser")
    # 행 정보를 모을 빈 리스트를 만든다
    rows = []
    # 팀 한 칸(tr.team)마다 반복한다
    for tr in soup.select("tr.team"):
        # 칸 안에 링크(a 태그)가 있는지 찾는다
        link = tr.select_one("a[href]")
        # 링크가 있으면 그 페이지 주소 기준으로 전체 주소를 만들고, 없으면 빈 글자로 둔다
        detail_url = urljoin(page_url, link["href"]) if link is not None else ""
        # 한 행의 값을 정해진 열 이름으로 담는다
        rows.append({
            # 팀 이름 (앞뒤 공백만 정리)
            "name": cell_text(tr, "name"),
            # 시즌 연도 글자 그대로
            "year_raw": cell_text(tr, "year"),
            # 승리 수 글자 그대로
            "wins_raw": cell_text(tr, "wins"),
            # 상세 페이지 전체 주소
            "detail_url": detail_url,
            # 수집 시점 (한국 시간)
            "scraped_at": scraped_at,
            # 득점 수 글자 그대로
            "goals_for_raw": cell_text(tr, "gf"),
        })
    # 뽑은 행 목록을 돌려준다
    return rows


# 모든 페이지의 행을 모을 빈 리스트를 만든다
all_rows = []
# 1페이지부터 최대 페이지까지 차례로 반복한다
for page in range(1, MAX_PAGES + 1):
    # 첫 페이지가 아니면 요청 전에 1초 쉰다
    if page > 1:
        time.sleep(1)
    # 이번 페이지 주소를 만든다
    page_url = PAGE_URL.format(page)
    # 페이지를 요청한다 (브라우저 흉내 헤더, 20초 제한)
    response = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    # 페이지에 맞춰 응답 인코딩을 정한다
    response.encoding = pick_encoding(response)
    # 수집 시점을 한국 시간으로 기록한다
    scraped_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    # 상태 코드가 200일 때만 행을 뽑는다
    rows = parse_rows(response.text, response.url, scraped_at) if response.status_code == 200 else []
    # 실제로 연 주소, 응답 상태, 그 페이지 행 수를 한 줄로 출력한다
    print(f"{page}페이지 | 주소: {response.url} | 상태: {response.status_code} | 행 수: {len(rows)}")
    # 200이 아니거나 0행이면 여기서 멈춘다
    if response.status_code != 200 or len(rows) == 0:
        # 몇 페이지에서 멈췄는지 출력한다
        print(f"{page}페이지에서 멈춤 (200이 아니거나 0행)")
        # 반복을 끝낸다
        break
    # 이번 페이지 행을 전체 목록에 더한다
    all_rows.extend(rows)
    # 합계가 기준 행 수 이상이면 멈춘다
    if len(all_rows) >= MIN_TOTAL_ROWS:
        # 멈춘 이유를 출력한다
        print(f"합계 {len(all_rows)}행으로 {MIN_TOTAL_ROWS}행 이상이 되어 {page}페이지에서 멈춤")
        # 반복을 끝낸다
        break

# 모은 행으로 표를 만들고 열 순서를 고정한다 (모든 값은 글자로 둔다)
df = pd.DataFrame(all_rows, columns=COLUMNS, dtype="string")
# 합계 행 수를 출력한다
print("합계 행 수:", len(df))
# 서로 다른 detail_url 개수를 출력한다 (빈 글자도 하나의 값으로 센다)
print("서로 다른 detail_url 개수:", df["detail_url"].nunique())

# 모은 행이 없으면 저장하지 않고 끝낸다
if len(df) == 0:
    # 중단 이유를 출력한다
    print("0행이므로 CSV를 만들지 않습니다.")
    # 프로그램을 종료한다
    raise SystemExit(1)

# 저장 폴더가 없으면 만든다
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
# CSV로 저장한다 (인덱스 제외, 엑셀에서 한글이 안 깨지도록 utf-8-sig)
df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
# 저장 위치를 출력한다
print("저장:", OUT_PATH)

# 표 출력 시 열이 잘리지 않도록 너비 설정을 넓힌다
pd.set_option("display.width", 250)
# 모든 열을 다 보여 주도록 설정한다
pd.set_option("display.max_columns", None)
# 표본 행 번호: 첫 행, 가운데 행(행 수 // 2), 마지막 행
sample_idx = [0, len(df) // 2, len(df) - 1]
# 표본 행 번호를 출력한다
print("표본 행 번호:", sample_idx)
# 표본 3행을 행 번호와 모든 열로 출력한다
print(df.iloc[sample_idx])
