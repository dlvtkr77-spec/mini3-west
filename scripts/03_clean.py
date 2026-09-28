# 파일 경로를 다루기 위해 pathlib에서 Path를 불러온다
from pathlib import Path

# 표를 다루기 위해 pandas를 불러온다
import pandas as pd

# 프로젝트 폴더(스크립트 위치의 한 단계 위)를 정한다
BASE = Path(__file__).resolve().parent.parent
# 읽을 원본 CSV 경로 (읽기만 하고 고치지 않는다)
RAW_PATH = BASE / "data" / "raw.csv"
# 저장할 정제 CSV 경로
CLEAN_PATH = BASE / "data" / "clean.csv"
# 원본 열 이름과 순서
RAW_COLUMNS = ["name", "year_raw", "wins_raw", "detail_url", "scraped_at", "goals_for_raw"]

# 표 출력 시 열이 잘리지 않도록 너비를 넓힌다
pd.set_option("display.width", 250)
# 모든 열을 다 보여 주도록 설정한다
pd.set_option("display.max_columns", None)


# 칸이 비었는지(NaN 또는 공백뿐인 글자) 판단하는 함수
def is_blank(series):
    # 글자 열이면 NaN이거나 앞뒤 공백을 지운 뒤 빈 글자인 칸을 빈칸으로 본다
    if series.dtype == object or pd.api.types.is_string_dtype(series):
        return series.isna() | (series.astype("string").str.strip() == "")
    # 숫자·범주 열이면 NaN만 빈칸으로 본다
    return series.isna()


# 표 하나의 요약 수치를 모으는 함수
def summarize(df, name_col, year_col):
    # detail_url의 빈칸 여부를 구한다
    url_blank = is_blank(df["detail_url"])
    # 요약 값을 사전으로 돌려준다
    return {
        # 전체 행 수
        "행 수": len(df),
        # detail_url 빈칸 수
        "detail_url 빈칸 수": int(url_blank.sum()),
        # detail_url 중복 수 (빈칸 포함, 첫 등장 제외)
        "detail_url 중복 수(빈칸 포함)": int(df["detail_url"].duplicated().sum()),
        # detail_url 중복 수 (빈칸 제외)
        "detail_url 중복 수(빈칸 제외)": int(df.loc[~url_blank, "detail_url"].duplicated().sum()),
        # name과 연도 조합의 중복 수 (첫 등장 제외)
        "name+year_raw 조합 중복 수": int(df.duplicated(subset=[name_col, year_col]).sum()),
    }


# 원본 CSV를 모든 값 글자 그대로 읽는다 (빈칸도 빈 글자로 둔다)
raw = pd.read_csv(RAW_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
# 열 이름이 예상과 같은지 확인한다
assert list(raw.columns) == RAW_COLUMNS, f"열 이름이 다릅니다: {list(raw.columns)}"
# 처리 전 요약을 구한다 (name, year_raw 원문 기준)
before = summarize(raw, "name", "year_raw")
# 처리 전 데이터형을 기록한다
before_dtypes = raw.dtypes.astype(str)
# 처리 전 열별 빈칸 수를 기록한다
before_blanks = pd.Series({c: int(is_blank(raw[c]).sum()) for c in raw.columns})

# 원본을 복사해 작업용 표를 만든다 (원본 표는 그대로 둔다)
df = raw.copy()
# 규칙 4: name 앞뒤 공백을 정리한다
df["name"] = df["name"].str.strip()
# 규칙 1: wins_raw 앞뒤 공백을 정리하고 숫자로 바꿔 wins 열에 넣는다 (못 바꾸면 NaN)
df["wins"] = pd.to_numeric(df["wins_raw"].str.strip(), errors="coerce")
# 규칙 2: goals_for_raw 앞뒤 공백을 정리하고 숫자로 바꿔 goals_for 열에 넣는다 (못 바꾸면 NaN)
df["goals_for"] = pd.to_numeric(df["goals_for_raw"].str.strip(), errors="coerce")
# 규칙 3: year_raw 앞뒤 공백을 정리하고 문자열 범주형으로 바꿔 year 열에 넣는다
df["year"] = df["year_raw"].str.strip().astype("category")

# 숫자로 못 바꾼 값의 원문 목록을 출력한다
print("== 숫자로 못 바꾼 원문 목록 ==")
# 못 바꾼 값을 셀 변수를 만든다
bad_count = 0
# wins와 goals_for 두 열을 차례로 본다
for new_col, raw_col in [("wins", "wins_raw"), ("goals_for", "goals_for_raw")]:
    # 변환 결과가 NaN인 행을 찾는다
    bad = df[df[new_col].isna()]
    # 그런 행마다 행 번호와 원문을 출력한다
    for idx, value in bad[raw_col].items():
        # 원문은 따옴표로 감싸 공백까지 보이게 출력한다
        print(f"  행 {idx} | {raw_col} 원문: {value!r}")
        # 개수를 하나 늘린다
        bad_count += 1
# 하나도 없으면 없다고 출력한다
if bad_count == 0:
    print("  (없음)")

# 규칙 5: name·wins·goals_for 중 빈칸인 행과 사유를 모은다
blank_reasons = []
# 행마다 빈칸 사유를 확인한다
for idx, row in df.iterrows():
    # 이 행의 사유를 모을 리스트
    reasons = []
    # name이 빈 글자면 사유를 더한다
    if row["name"] == "":
        reasons.append("name 빈칸")
    # wins가 NaN이면 원문과 함께 사유를 더한다
    if pd.isna(row["wins"]):
        reasons.append(f"wins 숫자 변환 실패(원문 {row['wins_raw']!r})")
    # goals_for가 NaN이면 원문과 함께 사유를 더한다
    if pd.isna(row["goals_for"]):
        reasons.append(f"goals_for 숫자 변환 실패(원문 {row['goals_for_raw']!r})")
    # 사유가 하나라도 있으면 목록에 넣는다
    if reasons:
        blank_reasons.append((idx, row["name"], row["year_raw"], "; ".join(reasons)))

# 빈칸 때문에 뺄 행을 먼저 출력한다
print("\n== 빈칸(또는 숫자 변환 실패)으로 뺀 행 ==")
# 뺄 행마다 행 번호, 이름, 연도, 사유를 출력한다
for idx, name, year_raw, reason in blank_reasons:
    print(f"  행 {idx} | name={name!r} | year_raw={year_raw!r} | 사유: {reason}")
# 하나도 없으면 없다고 출력한다
if not blank_reasons:
    print("  (없음)")
# 출력한 뒤 해당 행을 뺀다
df = df.drop(index=[r[0] for r in blank_reasons])

# 규칙 7: name과 연도 조합이 겹치는 행 중 처음 한 행을 뺀 나머지를 찾는다 (공백 정리한 값 기준)
dup_mask = df.duplicated(subset=["name", "year"], keep="first")
# 겹쳐서 뺄 행을 먼저 출력한다
print("\n== name+year_raw 조합이 겹쳐 뺀 행 (처음 한 행만 남김) ==")
# 뺄 행마다 행 번호, 이름, 연도, 사유를 출력한다
for idx, row in df[dup_mask].iterrows():
    # 처음 남긴 행의 번호를 찾는다
    first_idx = df[(df["name"] == row["name"]) & (df["year"] == row["year"])].index[0]
    # 사유와 함께 출력한다
    print(f"  행 {idx} | name={row['name']!r} | year_raw={row['year_raw']!r} | 사유: 행 {first_idx}와 조합 중복")
# 하나도 없으면 없다고 출력한다
if not dup_mask.any():
    print("  (없음)")
# 출력한 뒤 중복 행을 뺀다
df = df[~dup_mask]

# 규칙 6: detail_url은 빈칸이어도 빼지 않고, detail_url 기준 중복 제거도 하지 않는다 (아무 처리 없음)

# 원본 열 뒤에 새 열을 붙인 순서로 정한다
df = df[RAW_COLUMNS + ["wins", "goals_for", "year"]]
# 처리 후 요약을 구한다 (공백 정리한 name, year 기준)
after = summarize(df, "name", "year")
# 처리 후 데이터형을 기록한다
after_dtypes = df.dtypes.astype(str)
# 처리 후 열별 빈칸 수를 기록한다
after_blanks = pd.Series({c: int(is_blank(df[c]).sum()) for c in df.columns})

# 처리 전후 요약을 나란히 출력한다
print("\n== 처리 전후 요약 ==")
print(pd.DataFrame({"처리 전": before, "처리 후": after}))
# 처리 전후 데이터형과 빈칸 수를 열별로 나란히 출력한다 (새 열은 처리 전에 없으므로 '-')
print("\n== 열별 데이터형 · 빈칸 수 ==")
print(pd.DataFrame({
    # 처리 전 데이터형
    "전 dtype": before_dtypes,
    # 처리 후 데이터형
    "후 dtype": after_dtypes,
    # 처리 전 빈칸 수
    "전 빈칸": before_blanks.astype(object),
    # 처리 후 빈칸 수
    "후 빈칸": after_blanks,
}).reindex(df.columns).astype(object).fillna("-"))

# 정제한 표를 CSV로 저장한다 (인덱스 제외, utf-8-sig)
df.to_csv(CLEAN_PATH, index=False, encoding="utf-8-sig")
# 저장 위치를 출력한다
print("\n저장:", CLEAN_PATH)
