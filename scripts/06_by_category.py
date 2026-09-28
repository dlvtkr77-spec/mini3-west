# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path

# 화면 없이 파일로만 그리도록 matplotlib 백엔드를 Agg로 정한다
import matplotlib
# pyplot을 불러오기 전에 백엔드를 지정한다
matplotlib.use("Agg")
# 그림을 그리기 위해 pyplot을 불러온다
import matplotlib.pyplot as plt
# 표를 다루기 위해 pandas를 불러온다
import pandas as pd

# 프로젝트 폴더(스크립트 위치의 한 단계 위)를 정한다
BASE = Path(__file__).resolve().parent.parent
# 읽을 정제 CSV 경로 (읽기만 한다)
CLEAN_PATH = BASE / "data" / "clean.csv"
# 저장할 그림 경로
OUT_PATH = BASE / "charts" / "by_category.png"
# 가로축 시즌 순서 (이 순서 그대로 쓴다)
SEASONS = ["1990", "1991", "1992"]

# 막대 색 (기본 팔레트의 파랑)
BAR_COLOR = "#2a78d6"
# 그림 바탕색
SURFACE = "#fcfcfb"
# 주 글자색
TEXT_PRIMARY = "#0b0b0b"
# 보조 글자색 (축·눈금)
TEXT_SECONDARY = "#52514e"

# clean.csv를 pandas 기본 설정으로 읽는다 (year가 int64로 추론될 수 있다)
df = pd.read_csv(CLEAN_PATH, encoding="utf-8-sig")
# 읽은 year의 데이터형을 출력한다
print("읽은 year 데이터형:", df["year"].dtype)
# year를 글자로 바꾼 뒤 정해진 순서의 시즌 범주형으로 만든다
df["season"] = pd.Categorical(df["year"].astype(str), categories=SEASONS, ordered=True)
# 정해진 시즌에 들지 않는 값의 개수를 센다 (범주 밖이면 NaN이 된다)
unknown = int(df["season"].isna().sum())
# 범주 밖 값 개수를 출력한다
print("시즌 범주 밖 값:", unknown)
# clean.csv 전체 행 수를 구한다
n = len(df)

# 시즌별 wins 개수·합·평균을 구한다 (값이 없는 시즌도 남긴다)
grouped = df.groupby("season", observed=False)["wins"].agg(["count", "sum", "mean"])

# 빈 줄을 출력한다
print()
# 표 머리줄을 출력한다
print("| 시즌 | 개수 | 합 | 평균 |")
# 표 구분줄을 출력한다
print("|---|---|---|---|")
# 시즌마다 한 줄씩 출력한다
for season, row in grouped.iterrows():
    # 개수가 0이면 합과 평균을 "자료 없음"으로 적는다
    if row["count"] == 0:
        print(f"| {season} | 0 | 자료 없음 | 자료 없음 |")
    # 값이 있으면 평균을 소수 둘째 자리까지 적는다
    else:
        print(f"| {season} | {int(row['count'])} | {int(row['sum'])} | {row['mean']:.2f} |")

# 빈 줄을 출력한다
print()
# 개수 합을 구한다
count_sum = int(grouped["count"].sum())
# 개수 합과 clean 행 수를 나란히 출력하고 같음/다름을 적는다
print(f"개수 합 {count_sum} / clean 행 수 {n} → {'같음' if count_sum == n else '다름'}")

# 그림과 축을 만든다 (가로 7인치, 세로 5인치)
fig, ax = plt.subplots(figsize=(7, 5), facecolor=SURFACE)
# 축 바탕색을 정한다
ax.set_facecolor(SURFACE)
# 시즌 위치를 0, 1, 2로 정한다
positions = list(range(len(SEASONS)))
# 값이 있는 시즌만 막대로 그린다
for pos, season in zip(positions, SEASONS):
    # 이 시즌의 요약 값을 꺼낸다
    row = grouped.loc[season]
    # 자료가 없으면 막대를 그리지 않는다
    if row["count"] == 0:
        continue
    # 평균 높이의 막대를 그린다
    bar = ax.bar(pos, row["mean"], width=0.6, color=BAR_COLOR)
    # 막대 위에 평균과 n을 두 줄로 적는다
    ax.bar_label(bar, labels=[f"{row['mean']:.2f}\nn = {int(row['count'])}"],
                 padding=4, color=TEXT_PRIMARY, fontsize=11)
# 가로축 눈금 위치를 시즌 순서대로 정한다
ax.set_xticks(positions)
# 가로축 눈금 글자를 시즌 이름으로 정한다
ax.set_xticklabels(SEASONS)
# 가로축 이름을 적는다
ax.set_xlabel("Season", color=TEXT_SECONDARY)
# 세로축 이름을 적는다
ax.set_ylabel("Average wins", color=TEXT_SECONDARY)
# 제목을 적는다 (clean 행 수 포함)
ax.set_title(f"Average wins by season (n = {n})", color=TEXT_PRIMARY, loc="left", fontsize=13)
# 세로축은 0부터 시작하고 글자가 잘리지 않게 위쪽 여유를 준다
ax.set_ylim(0, grouped["mean"].max() * 1.2)
# 옅은 가로 격자선을 그린다
ax.grid(axis="y", color="#e5e4e0", linewidth=0.8)
# 격자선을 막대 뒤로 보낸다
ax.set_axisbelow(True)
# 위쪽·오른쪽·왼쪽 테두리를 없앤다
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
# 아래 테두리 색을 옅게 한다
ax.spines["bottom"].set_color(TEXT_SECONDARY)
# 눈금 글자색을 정한다
ax.tick_params(colors=TEXT_SECONDARY, length=0)
# 여백을 자동으로 맞춘다
fig.tight_layout()

# charts 폴더가 없으면 만든다
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
# 그림을 파일로 저장한다 (plt.show는 쓰지 않는다)
fig.savefig(OUT_PATH, dpi=150, facecolor=SURFACE)
# 그림 메모리를 닫는다
plt.close(fig)
# 저장 위치를 출력한다
print("저장:", OUT_PATH)
