from pykiwoom.kiwoom import *
import time

# 로그인
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)
print("로그인 완료")

# 뉴스 검색 설정
search_query = "증시요약 특징 상한가"
news_code = "0700"  # 종합시황뉴스

# 뉴스 검색
kiwoom.SetInputValue("검색어", search_query)
kiwoom.SetInputValue("종류", news_code)
kiwoom.CommRqData("news_search", "opw00094", 0, "1000")

# 조회 결과가 수신될 때까지 기다림
while kiwoom.remained_data:
    time.sleep(0.2)

# 수신된 데이터 출력
news_data = kiwoom.GetCommDataEx("news_search", "opw00094")
for i, data in enumerate(news_data):
    date = data[0]
    time = data[1]
    title = data[2]
    print(f"{i+1}. [{date} {time}] {title}")
