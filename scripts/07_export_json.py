# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path
# JSON 파일을 다시 읽기 위해 json을 불러온다
import json

# 표를 다루기 위해 pandas를 불러온다
import pandas as pd

# 프로젝트 폴더(스크립트 위치의 한 단계 위)를 정한다
BASE = Path(__file__).resolve().parent.parent
# 읽을 정제 CSV 경로 (읽기만 한다)
CLEAN_PATH = BASE / "data" / "clean.csv"
# 저장할 JSON 경로
JSON_PATH = BASE / "data" / "data.json"
# JSON에 담을 열과 순서
COLUMNS = ["name", "year", "wins", "goals_for"]

# clean.csv를 읽는다 (year는 시즌 범주이므로 글자로 읽는다)
df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig", dtype={"year": str})
# 필요한 네 열만 고른다
out = df[COLUMNS]

# 한 행을 한 묶음으로 하는 목록 모양(records)으로 JSON 저장 (한글 그대로, 들여쓰기 2칸)
out.to_json(JSON_PATH, orient="records", force_ascii=False, indent=2)
# 저장 위치를 출력한다
print("저장:", JSON_PATH)

# 저장한 data.json을 utf-8로 다시 읽는다
with open(JSON_PATH, encoding="utf-8") as f:
    # JSON 목록을 파이썬 리스트로 바꾼다
    items = json.load(f)

# 항목 수와 clean.csv 행 수를 나란히 출력하고 같음/다름을 적는다
print(f"data.json 항목 수 {len(items)} / clean.csv 행 수 {len(df)} → {'같음' if len(items) == len(df) else '다름'}")

# 빈 줄을 출력한다
print()
# 비교표 머리줄을 출력한다
print("| 열 | data.json 첫 항목 | clean.csv 첫 줄 | 같음/다름 |")
# 비교표 구분줄을 출력한다
print("|---|---|---|---|")
# 네 열을 차례로 비교한다
for col in COLUMNS:
    # data.json 첫 항목의 값을 꺼낸다
    json_value = items[0][col]
    # clean.csv 첫 줄의 값을 꺼낸다
    csv_value = df.loc[0, col]
    # 두 값을 글자로 바꿔 같은지 비교한다
    same = "같음" if str(json_value) == str(csv_value) else "다름"
    # 값과 파이썬 형 이름을 함께 출력한다
    print(f"| {col} | {json_value!r} ({type(json_value).__name__}) | {csv_value!r} | {same} |")
