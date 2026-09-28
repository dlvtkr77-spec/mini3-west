# pandas 라이브러리를 pd라는 이름으로 불러온다
import pandas as pd

# 누가 봐도 가짜인 팀 이름 3개를 리스트로 만든다
teams = ["가짜팀 알파", "가짜팀 베타", "가짜팀 감마"]
# 각 팀의 승리 수를 숫자로 만든다
wins = [10, 7, 3]

# 팀 이름과 승리 수 열을 가진 표(DataFrame)를 만든다
df = pd.DataFrame({"팀 이름": teams, "승리 수": wins})

# 표 위에 안내 문구를 출력한다
print("환경 확인용 가상 예시")
# 표 전체를 출력한다
print(df)
# 표의 (행 수, 열 수)를 출력한다
print(df.shape)
