# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path
# 상대 주소를 전체 주소로 바꾸기 위해 urljoin을 불러온다
from urllib.parse import urljoin
# 수집 시각을 기록하기 위해 datetime을 불러온다
from datetime import datetime
# 한국 시간대를 쓰기 위해 ZoneInfo를 불러온다
from zoneinfo import ZoneInfo

# 웹 페이지 요청용 requests를 불러온다
import requests
# HTML 해석용 BeautifulSoup을 불러온다
from bs4 import BeautifulSoup
# 표를 만들고 CSV로 저장하기 위해 pandas를 불러온다
import pandas as pd

# 수집할 목록 페이지 주소 (이 페이지 하나만 요청한다)
LIST_URL = "https://www.scrapethissite.com/pages/forms/?page_num=1"
# 사용자가 화면에서 센 항목 수 (비교용)
EXPECTED_COUNT = 25
# 스크립트 파일 위치 기준 ../data/raw_p1.csv 경로를 만든다
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_p1.csv"
# 저장할 열 이름과 순서를 정한다
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


# 목록 페이지를 한 번 요청한다 (브라우저 흉내 헤더, 20초 제한)
response = requests.get(LIST_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
# 페이지에 맞춰 응답 인코딩을 정한다
response.encoding = pick_encoding(response)
# 응답 상태 코드를 출력한다
print("상태 코드:", response.status_code)
# 사용한 인코딩을 출력한다
print("인코딩:", response.encoding)

# 상태 코드가 200이 아니면 CSV를 만들지 않고 끝낸다
if response.status_code != 200:
    # 중단 이유를 출력한다
    print("200이 아니므로 CSV를 만들지 않습니다.")
    # 프로그램을 종료한다
    raise SystemExit(1)

# 수집 시점을 한국 시간으로 기록한다
scraped_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
# 응답 글자를 BeautifulSoup으로 해석한다
soup = BeautifulSoup(response.text, "html.parser")

# 행 정보를 모을 빈 리스트를 만든다
rows = []
# 팀 한 칸(tr.team)마다 반복한다
for tr in soup.select("tr.team"):
    # 칸 안에 링크(a 태그)가 있는지 찾는다
    link = tr.select_one("a[href]")
    # 링크가 있으면 목록 주소 기준으로 전체 주소를 만들고, 없으면 빈 글자로 둔다
    detail_url = urljoin(LIST_URL, link["href"]) if link is not None else ""
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

# 모은 행으로 표를 만들고 열 순서를 고정한다 (모든 값은 글자로 둔다)
df = pd.DataFrame(rows, columns=COLUMNS, dtype="string")
# 행 수를 출력한다
print("행 수:", len(df))
# 사용자가 센 항목 수와 같은지 출력한다
print(f"화면에서 센 수({EXPECTED_COUNT})와 일치:", len(df) == EXPECTED_COUNT)
# detail_url이 채워진 행 수를 출력한다
print("detail_url 있는 행 수:", int((df["detail_url"] != "").sum()))

# 0행이면 CSV를 만들지 않고 끝낸다
if len(df) == 0:
    # 중단 이유를 출력한다
    print("0행이므로 CSV를 만들지 않습니다.")
    # 프로그램을 종료한다
    raise SystemExit(1)

# 표 출력 시 열이 잘리지 않도록 너비 설정을 넓힌다
pd.set_option("display.width", 200)
# 모든 열을 다 보여 주도록 설정한다
pd.set_option("display.max_columns", None)
# 앞 3행을 출력한다
print(df.head(3))

# 저장 폴더가 없으면 만든다
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
# CSV로 저장한다 (인덱스 제외, 엑셀에서 한글이 안 깨지도록 utf-8-sig)
df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
# 저장 위치를 출력한다
print("저장:", OUT_PATH)
