import sys
import datetime
import logging

from crawl_data import *

logging.basicConfig(filename='log/krxstock.log', level=logging.DEBUG)


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

    # MySQL 연결 설정
    conn = connect_db()

    code_list = scrap_stock_data(start_date, end_date)

try:
    insert_stock_trading_data(conn, code_list)
except Exception as e:
    logging.error(str(e))
    traceback.print_exc()
finally:
    # Connection 닫기
    conn.close()
