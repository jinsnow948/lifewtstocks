import sys
import traceback
from config.db_handle import *
from pykrx import stock


if __name__ == "__main__":

    try:
        # MySQL 연결 설정
        conn = connect_db()

        create_stock_ticker(conn);

        stock_data = stock.get_market_ticker_list(market="ALL")
        print(stock_data)

        execute_insert_query(conn,f"DELETE FROM stock_ticker")

        for code in stock_data:
            name = stock.get_market_ticker_name(code)

            execute_insert_query(conn,f"INSERT INTO stock_ticker (ticker, stock_name) VALUES ('{code}', '{name}')")

    except Exception as e:
        tb = traceback.format_exc()
        line_number = sys.exc_info()[-1].tb_lineno
        print(f"Error occurred at line {line_number}: {e}\n{tb}")
