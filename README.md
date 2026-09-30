# 하키 팀 비교 도우미

## 1. 무엇을 하나

하키를 처음 보는 사용자가 **시즌**과 **최소 승리 수**를 입력하면, 조건에 맞는 팀-시즌 기록을 카드로 모아 비교할 수 있는 화면입니다. 카드는 승리 수가 많은 순서로 보여 줍니다.

"이 조건으로 추천받기"를 누르면 조건에 맞는 후보 중에서 AI가 팀-시즌 기록 하나를 추천하고, 그 기록의 **승리 수**와 **득점**을 들어 이유를 두 줄로 보여줍니다. 추천된 카드에는 "AI 추천" 표시가 붙습니다.

## 2. 배포 주소

https://mini3-west.vercel.app

## 3. 데이터

| 항목 | 내용 |
|---|---|
| 출처 | [Scrape This Site 하키 팀 목록](https://www.scrapethissite.com/pages/forms/) |
| 수집 범위 | 목록 1~2페이지 |
| 수집 시점 | 2026-09-28 |
| 행 수 | 원본 50행 (`data/raw.csv`) · 정제 50행 (`data/clean.csv`) · JSON 50항목 (`data/data.json`) |
| 화면에 사용하는 열 | `name` · `year` · `wins` · `goals_for` |

원본의 `wins_raw`와 `goals_for_raw`는 글자로 수집되어, 정제 단계에서 숫자 열 `wins`와 `goals_for`로 바꿨습니다. 정제하면서 뺀 행은 없습니다.

## 4. AI 추천

- 모델: Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`)
- 전달하는 값: 적용한 조건(시즌, 최소 승리 수)과, 조건에 맞는 후보를 `wins`가 높은 순으로 정렬한 최대 5개의 `name` · `year` · `wins` · `goals_for`
- 받는 값: 후보 중 `name`과 `year`가 모두 일치하는 기록 하나와 이유 두 줄
- 추천을 표시하지 않는 경우: 아래 중 하나라도 해당하면 추천 대신 안내 문장을 보여줍니다. 서버(`api/recommend.js`)와 브라우저(`index.html`)가 같은 검사를 한 번씩 합니다.
  - 추천한 기록이 전달한 후보 밖에 있을 때
  - 이유가 정확히 두 줄이 아닐 때
  - 이유에 고른 기록의 `wins`·`goals_for`가 아닌 숫자가 있거나, 두 숫자 중 하나가 빠졌을 때
- 표에 없는 정보: 선수, 경기 내용, 현재 성적처럼 후보 표에 없는 정보는 말하지 말라고 AI 지시문에 적어 두었습니다. 코드로 자동 검사하는 것은 위의 숫자까지입니다.
- 후보가 0개일 때: AI를 호출하지 않습니다. 카드 자리에 해당 범위의 최대 승리 수와 조건을 낮추라는 안내만 표시합니다.
- API 키: 코드에 넣지 않고 Vercel 환경변수 `GEMINI_API_KEY`로 관리합니다.

## 5. 확인한 것

| 조건 | 결과 |
|---|---|
| 시즌 1992 · 최소 40승 | 후보 4개 (Boston Bruins 51승 · Chicago Blackhawks 47승 · Detroit Red Wings 47승 · Calgary Flames 43승) |
| 시즌 1992 · 최소 50승 | 후보 1개 (Boston Bruins 51승) |
| 시즌 1992 · 최소 52승 | 후보 0개 · AI를 호출하지 않고 안내 표시 |

- 정상 조건(1992 · 최소 40승)과 후보 1개 조건(1992 · 최소 50승)에서 **Boston Bruins · 1992**가 추천됐습니다. 이유에 나온 51승 · 332득점은 `data/data.json`의 값과 같습니다.
- 시즌 1990 · 최소 45승 조건의 후보는 Chicago Blackhawks 49승 · St. Louis Blues 47승 · Calgary Flames 46승 · Los Angeles Kings 46승으로, 1992 · 최소 40승의 후보와 다릅니다.
- 배포된 페이지 소스에서 `GEMINI_API_KEY`와 키 값은 찾아지지 않았습니다.
- `.env`는 `.gitignore`에 들어 있어 GitHub에 올라가지 않습니다.

## 6. 한계

- 목록의 처음 2페이지에 있는 50개 팀-시즌 기록만 사용합니다.
- 1992 시즌은 7개 기록만 들어 있어 그 시즌 전체를 대표하지 않을 수 있습니다.
- 과거 시즌(1990~1992) 자료이므로 현재 팀 성적을 나타내지 않습니다.
- 원본 사이트에 팀별 상세 페이지가 없어서, "원래 목록 보기"는 해당 기록이 있는 목록 페이지(1페이지 또는 2페이지)로 연결합니다.
- Gemini API 사용 한도를 넘으면 추천이 일시적으로 실패할 수 있습니다. 이때는 "추천을 불러오지 못했습니다. 잠시 뒤 다시 눌러 주세요."가 표시됩니다.

## 실행 안내

### 1. 다시 모으기

`scripts` 폴더의 파일을 번호 순서대로 실행합니다. 프로젝트 폴더에서 맥 터미널에 명령을 입력합니다.

| 순서 | 파일 | 만드는 것 | 맥 명령 | 확인 |
|---|---|---|---|---|
| 0 | `scripts/00_env_check.py` | 파일 없음 · pandas가 동작하는지 가상 예시 표를 화면에 출력 | `python3 scripts/00_env_check.py` | 확인 안 함 |
| 1 | `scripts/01_collect_p1.py` | `data/raw_p1.csv` (목록 1페이지) · 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python3 scripts/01_collect_p1.py` | 확인 안 함 |
| 2 | `scripts/02_collect.py` | `data/raw.csv` (합계 50행이 되면 멈춤) · 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python3 scripts/02_collect.py` | 확인 안 함 |
| 3 | `scripts/03_clean.py` | `data/clean.csv` | `python3 scripts/03_clean.py` | 확인함 · 정제 50행 |
| 4 | `scripts/04_stats.py` | 파일 없음 · `wins` 통계 표를 화면에 출력 | `python3 scripts/04_stats.py` | 확인 안 함 |
| 5 | `scripts/05_hist.py` | `charts/hist.png` | `python3 scripts/05_hist.py` | 확인 안 함 |
| 6 | `scripts/06_by_category.py` | `charts/by_category.png` | `python3 scripts/06_by_category.py` | 확인 안 함 |
| 7 | `scripts/07_export_json.py` | `data/data.json` | `python3 scripts/07_export_json.py` | 확인 안 함 |

`03_clean.py` 실행 결과: 오류 없이 완료 · 처리 전 50행 · 처리 후 50행 · 제외 0행 · 숫자 변환 실패 없음 · 저장 `data/clean.csv`

### 2. 화면에 반영하기

1. 새로 만든 `data/data.json`과 `charts`의 그림(`charts/hist.png` · `charts/by_category.png`)을 커밋합니다.
2. `main` 브랜치에 푸시하면 Vercel이 자동으로 다시 배포합니다.
3. Vercel에서 배포 상태가 **Ready**가 된 뒤 https://mini3-west.vercel.app 에서 확인합니다.

### 3. AI 연결

AI 추천은 서버 함수 `api/recommend.js`가 처리합니다. 이 함수는 환경변수 `GEMINI_API_KEY`를 서버에서만 읽습니다.

1. Vercel 프로젝트의 **Settings → Environment Variables**에 `GEMINI_API_KEY`를 등록합니다. 키 값은 README나 코드에 적지 않습니다.
2. 등록한 뒤 **Redeploy**해야 새 환경변수가 적용됩니다.
