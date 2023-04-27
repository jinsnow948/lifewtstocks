import sys
import logging
from config.db_handle import *
from pykrx import stock
from datetime import datetime, timedelta

logging.basicConfig(filename='log/top100_theme.log',
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s')

if __name__ == "__main__":
    # start_date, end_date 인자값 체크
    if len(sys.argv) < 3:
        logging.error("Error: start_date와 end_date 인자를 입력해주세요.")
        sys.exit(1)

    try:
        start_date = datetime.strptime(sys.argv[1], '%Y%m%d')
        end_date = datetime.strptime(sys.argv[2], '%Y%m%d')
    except ValueError:
        logging.error("Error: 날짜 형식이 잘못되었습니다. (YYYYMMDD 형식으로 입력)")
        sys.exit(1)
    logging.info(f'start_date : {start_date}, end_date : {end_date}')

    try:
        # MySQL 연결 설정
        conn = connect_db()

        #create_market_price_change(conn)

        current_date = start_date

        while current_date <= end_date:
            insert_values = []
            current_date_str = current_date.strftime("%Y%m%d")
            
            # 전일 대비 등락률 상위 100 종목 조회
            top100 = stock.get_market_price_change_by_ticker(current_date_str, current_date_str)
            top100 = top100.sort_values(by="등락률", ascending=False).head(100)

            logging.info(top100)

            # 조회한 데이터를 리스트에 저장
            for ticker, row in top100.iterrows():
                reference_date = current_date.date()
                name = row["종목명"]
                opening_price = row["시가"]
                closing_price = row["종가"]
                price_change = row["변동폭"]
                percentage_change = row["등락률"]
                volume = row["거래량"]
                transaction_amount = row["거래대금"]

                insert_values.append(f"('{reference_date}', '{ticker}', '{name}', {opening_price}, {closing_price}, {price_change}, {percentage_change}, {volume}, {transaction_amount})")
            
            # DB에 한 번에 INSERT
            sql = f"""
            INSERT INTO market_price_change (
                reference_date, ticker, name, opening_price, closing_price, price_change, percentage_change, volume, transaction_amount)
            VALUES {', '.join(insert_values)}
            """
            
            execute_insert_query(conn, sql)

            # 다음 날짜로 이동
            current_date += timedelta(days=1)
    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f"Error occurred at line {sys.exc_info()[-1].tb_lineno}: {e}\n{tb}")
