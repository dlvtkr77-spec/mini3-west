# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path

# 화면 없이 파일로만 그리도록 matplotlib 백엔드를 Agg로 정한다
import matplotlib
# pyplot을 불러오기 전에 백엔드를 지정한다
matplotlib.use("Agg")
# 그림을 그리기 위해 pyplot을 불러온다
import matplotlib.pyplot as plt
# 구간별 개수를 세기 위해 numpy를 불러온다
import numpy as np
# 표를 다루기 위해 pandas를 불러온다
import pandas as pd

# 프로젝트 폴더(스크립트 위치의 한 단계 위)를 정한다
BASE = Path(__file__).resolve().parent.parent
# 읽을 정제 CSV 경로 (읽기만 한다)
CLEAN_PATH = BASE / "data" / "clean.csv"
# 저장할 그림 경로
OUT_PATH = BASE / "charts" / "hist.png"
# 고정 구간 경계
BINS = [10, 20, 30, 40, 50, 60]

# 막대 색 (기본 팔레트의 파랑)
BAR_COLOR = "#2a78d6"
# 그림 바탕색
SURFACE = "#fcfcfb"
# 주 글자색
TEXT_PRIMARY = "#0b0b0b"
# 보조 글자색 (축·눈금)
TEXT_SECONDARY = "#52514e"

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
# clean.csv 전체 행 수를 구한다
n = len(df)

# wins 최솟값과 최댓값을 출력한다
print(f"wins 최소: {wins.min()} / 최대: {wins.max()}")
# 구간 경계 밖(10 미만 또는 60 초과)에 있는 값의 개수를 센다
outside = int(((wins < BINS[0]) | (wins > BINS[-1])).sum())
# 모든 값이 구간 경계 안에 드는지 출력한다
print(f"구간 [{BINS[0]}, {BINS[-1]}] 밖의 값: {outside}개 → {'모두 포함' if outside == 0 else '포함 안 되는 값 있음'}")

# 구간별 개수를 센다 (왼쪽 포함·오른쪽 미포함, 마지막 구간만 오른쪽 포함)
counts, edges = np.histogram(wins, bins=BINS)

# 빈 줄을 출력한다
print()
# 빈도표 머리줄을 출력한다
print("| 구간 | 개수 |")
# 빈도표 구분줄을 출력한다
print("|---|---|")
# 구간마다 한 줄씩 출력한다
for i, c in enumerate(counts):
    # 마지막 구간이면 오른쪽 괄호를 ]로, 아니면 )로 쓴다
    right = "]" if i == len(counts) - 1 else ")"
    # 구간과 개수를 출력한다
    print(f"| [{edges[i]}, {edges[i + 1]}{right} | {c} |")
# 합계 줄을 출력한다
print(f"| 합계 | {counts.sum()} |")

# 빈 줄을 출력한다
print()
# 빈도 합과 clean 행 수를 나란히 출력하고 같음/다름을 적는다
print(f"빈도 합 {counts.sum()} / clean 행 수 {n} → {'같음' if counts.sum() == n else '다름'}")

# 그림과 축을 만든다 (가로 8인치, 세로 5인치)
fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE)
# 축 바탕색을 정한다
ax.set_facecolor(SURFACE)
# 구간 폭만큼 막대를 그린다 (막대 사이 2px 틈을 위해 흰 테두리)
bars = ax.bar(edges[:-1], counts, width=np.diff(edges), align="edge",
              color=BAR_COLOR, edgecolor=SURFACE, linewidth=2)
# 막대 위에 개수를 적는다
ax.bar_label(bars, labels=[str(c) for c in counts], padding=3, color=TEXT_PRIMARY, fontsize=11)
# 가로축 눈금을 구간 경계로 정한다
ax.set_xticks(BINS)
# 가로축 이름을 적는다
ax.set_xlabel("Wins", color=TEXT_SECONDARY)
# 세로축 이름을 적는다
ax.set_ylabel("Number of team-seasons", color=TEXT_SECONDARY)
# 제목을 적는다 (clean 행 수 포함)
ax.set_title(f"NHL Team Seasons, pages 1-2 (n = {n})", color=TEXT_PRIMARY, loc="left", fontsize=13)
# 개수 글자가 잘리지 않도록 세로축 위쪽 여유를 준다
ax.set_ylim(0, counts.max() * 1.15)
# 세로축 눈금을 정수로만 표시한다
ax.yaxis.get_major_locator().set_params(integer=True)
# 옅은 가로 격자선을 막대 뒤에 그린다
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
