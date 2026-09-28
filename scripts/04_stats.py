# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path

# 표를 다루기 위해 pandas를 불러온다
import pandas as pd

# 스크립트 위치 기준으로 data/clean.csv 경로를 만든다 (읽기만 한다)
CLEAN_PATH = Path(__file__).resolve().parent.parent / "data" / "clean.csv"

# clean.csv를 읽는다 (_raw 열은 글자, year는 범주형으로 지정)
df = pd.read_csv(
    # 읽을 파일 경로
    CLEAN_PATH,
    # 엑셀용 BOM이 붙은 utf-8로 읽는다
    encoding="utf-8-sig",
    # 03_clean.py에서 의도한 데이터형을 다시 지정한다
    dtype={"year_raw": str, "wins_raw": str, "goals_for_raw": str, "year": "category"},
)

# wins 열을 꺼낸다
wins = df["wins"]
# 빈칸이 아닌 wins 값의 개수를 구한다
count = int(wins.count())
# 최솟값을 구한다
w_min = wins.min()
# 최댓값을 구한다
w_max = wins.max()
# 평균을 구한다
w_mean = wins.mean()
# 중앙값을 구한다
w_median = wins.median()


# 특정 wins 값을 가진 모든 행의 name, year, goals_for를 글자로 만드는 함수
def rows_with(value):
    # wins가 그 값과 같은 행을 모두 고른다
    hit = df[wins == value]
    # 행마다 "name (year, goals_for 값)" 모양으로 만든다
    parts = [f"{r['name']} (year {r['year']}, goals_for {r['goals_for']})" for _, r in hit.iterrows()]
    # 해당 행 수와 함께 세미콜론으로 이어 돌려준다
    return f"{len(hit)}행: " + "; ".join(parts)


# 마크다운 표 머리줄을 출력한다
print("| 항목 | 값 |")
# 마크다운 표 구분줄을 출력한다
print("|---|---|")
# 개수 줄을 출력한다
print(f"| 개수 | {count} |")
# 최소 줄을 해당 행 정보와 함께 출력한다
print(f"| 최소 | {w_min} — {rows_with(w_min)} |")
# 최대 줄을 해당 행 정보와 함께 출력한다
print(f"| 최대 | {w_max} — {rows_with(w_max)} |")
# 평균 줄을 소수 둘째 자리까지 출력한다
print(f"| 평균 | {w_mean:.2f} |")
# 중앙값 줄을 계산된 그대로 출력한다
print(f"| 중앙값 | {w_median} |")

# 빈 줄을 하나 출력한다
print()
# 전체 행 수를 구한다
total = len(df)
# 개수와 전체 행 수를 나란히 출력하고 같음/다름을 적는다
print(f"wins 개수 {count} / clean.csv 전체 행 수 {total} → {'같음' if count == total else '다름'}")

# 평균과 중앙값의 차이를 구한다
diff = w_mean - w_median
# 어느 쪽이 큰지 정한다
if diff > 0:
    bigger = "평균이 중앙값보다 큼"
# 중앙값이 더 크면
elif diff < 0:
    bigger = "중앙값이 평균보다 큼"
# 둘이 같으면
else:
    bigger = "평균과 중앙값이 같음"
# 비교 결과와 차이(절댓값, 소수 둘째 자리)를 한 줄로 출력한다
print(f"{bigger}, 차이 {abs(diff):.2f} (평균 {w_mean:.2f}, 중앙값 {w_median})")
