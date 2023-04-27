import logging
import os
import json

from flask import Flask, render_template, request, redirect, url_for, jsonify
from jinja2 import Environment
from config.db_handle import *

import datetime
import pymysql

app = Flask(__name__)
app.jinja_env.globals.update(min=min)
app.jinja_env.globals.update(max=max)


# Load the config file
with open('/home/jinwon/lifewtstocks/config/config.json') as f:
    config = json.load(f)

logging.basicConfig(filename='log/pageloader.log',
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s')

logging.getLogger("urllib3").setLevel(logging.CRITICAL)

conn = connect_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dailytrading', methods=['GET', 'POST'])
def trading_data():
    if request.method == 'POST':
        trading_data_len = None
        # Get form data
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        sort_by = request.form['sort_by']

        # Parse dates
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Query trading data
        with conn.cursor() as cursor:
            query = f"select code, stock_name as 종목명 , sum(foreign_total) as 외국인 , " \
                    f"sum(institution) as 기관 , sum(individual) as 개인 , " \
                    f"sum(foreign_total+institution+individual) as 총합 from stock_trading " \
                    f"WHERE trading_date BETWEEN '{start_date}' AND '{end_date}' group by code, 종목명 ORDER BY " \
                    f"{sort_by} DESC"
            cursor.execute(query)
            trading_data = cursor.fetchall()
            trading_data_len = len(trading_data)
        print(trading_data)

        # Render results template
        return render_template('dailytradingresults.html', trading_data=trading_data, start_date=start_date, end_date=end_date
                               , sort_by=sort_by , trading_data_len=trading_data_len)

    else:
        # Render form template
        return render_template('dailytrading.html')

@app.route('/news')
def news():
    code = request.args.get('code')
    print(code)
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    total_pages=0
    total_count=0
    news_results = []

    if code:
        try:
            with conn.cursor() as cursor:

                # Count total rows
                count_sql = """
                     SELECT COUNT(*) as count
                     FROM stock_trading AS st
                     LEFT JOIN stock_news ON stock_news.stock_name = st.stock_name
                                        AND stock_news.code = st.code
                                        AND stock_news.article_date = st.trading_date
                     WHERE st.code = '{}'
                     """.format(code)
                cursor.execute(count_sql)
                total_count = cursor.fetchone()['count']
                print(f'total_count: {total_count}')

                # Get data for the current page
                offset = (page - 1) * size

                sql = """
                    SELECT st.stock_name as stock_name, st.trading_date as trading_date, st.foreign_total as foreign_total, st.institution as institution, st.individual as individual,
                           COALESCE(stock_news.article_date, '') AS article_date,
                           COALESCE(stock_news.title, '') AS title,
                           COALESCE(stock_news.link, '') AS link
                    FROM stock_trading AS st
                    LEFT JOIN stock_news ON stock_news.stock_name = st.stock_name
                                       AND stock_news.code = st.code
                                       AND stock_news.article_date = st.trading_date
                    WHERE st.code = '{}'
                    ORDER BY st.trading_date desc
                    LIMIT {} OFFSET {}
                    """.format(code,size,offset)
                cursor.execute(sql)
                news_results = cursor.fetchall()

        except Exception as e:
            logging.error(f"Error executing SQL query: {e}")

    # Calculate total number of pages
    total_pages = (total_count + size - 1) // size
    print(f'total_pages: {total_pages}')


    # Render issues template
    return render_template('news.html', news_results=news_results, page=page, size=size, total_pages=total_pages)


@app.route('/issue')
def issue():
    stock_name = request.args.get('stock_name')
    results = []

    if stock_name:
        try:
            with conn.cursor() as cursor:
                sql = f"SELECT report_time , title, stock_name, news_content, news_link FROM stock_issues WHERE "\
                      f"stock_name like '%{stock_name}%' order by report_time desc"
                cursor.execute(sql)
                results = cursor.fetchall()
        except Exception as e:
            logging.error(f"Error executing SQL query: {e}")
        # Check if there are no results
    # Render issues template
    return render_template('issue.html', results=results, stock_name=stock_name)

@app.route('/search_stock', methods=['POST'])
def search_stock():
    search_query = request.form.get('query')
    try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT ticker, stock_name FROM stocks WHERE stock_name LIKE %s LIMIT 10", ("%" + search_query + "%",))
                results = cursor.fetchall()
    except Exception as e:
            logging.error(f"Error executing SQL query: {e}")

    return jsonify({'results': results})


@app.route('/theme_register', methods=['GET', 'POST'])
def theme_register():
    if request.method == 'POST':
        theme_name = request.form['theme_name']
        theme_detail_name = request.form.get('theme_detail_name') or None
        related_stock_code = request.form.get('related_stock_code') or None
        related_stock_name = request.form.get('related_stock_name') or None
        theme_occurrence_date = request.form.get('theme_occurrence_date') or None
        theme_description = request.form.get('theme_description') or None

        action = request.form.get('action')
        logging.info(action)

        if action == 'insert':
            try:
                with conn.cursor() as cursor:
                    query = '''INSERT INTO theme_info (theme_name, theme_detail_name, related_stock_code, related_stock_name, theme_occurrence_date, theme_description)
                              VALUES (%s, %s, %s, %s, %s, %s)'''
                    params = (theme_name, theme_detail_name, related_stock_code, related_stock_name, theme_occurrence_date, theme_description)
                    #converted_parameters = tuple(map(convert_none_to_null, params))
                    logging.info(f"SQL Query: {query}")
                    logging.debug(f"Parameters: {params}")
                    cursor.execute(query, params)
                    logging.info(f"{theme_name}이 insert 되었습니다!")
                    conn.commit()
            except Exception as e:
                logging.error("Error : {}".format(e))
        elif action == 'update':
            try:
                with conn.cursor() as cursor:
                    query = ''' UPDATE theme_info SET theme_detail_name = %s, theme_occurrence_date = %s, theme_description = %s where theme_name= %s, related_stock_code = %s'''
                    params = (theme_detail_name,theme_occurrence_date,theme_description,theme_name,related_stock_code)
                    cursor.execute(query,params)
                    logging.info(f"{theme_name}이 update 되었습니다!")
                    conn.commit()
            except Exception as e:
                logging.error(f"Error: {e}")
                traceback.print_exec()


        return redirect('/theme')  # 등록이 완료되면 원하는 페이지로 리다이렉트합니다.
    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute("select * from stock_ticker")
                stocks = cursor.fetchall()
        except Exception as e:
            logging.error(f"Error : {e}")
        return render_template('theme_register.html', stocks=stocks)


@app.route('/theme', methods=['GET','POST'])
def theme():
    if request.method == 'POST':
        # Get form data
        date_str = request.form['date']
        page = int(request.form.get('page', 1))
        

        # 페이지네이션 설정
        items_per_page = 20
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        # Parse dates
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        print(f'date {date}')
        
        results = []
        
        total_items=0
        
        try:
            with conn.cursor() as cursor:
                sql_count = "SELECT COUNT(*) as count FROM market_price_change WHERE reference_date = '{}'".format(date)
                cursor.execute(sql_count)
                total_items = cursor.fetchone()['count']

                print(total_items)

                # 페이징 처리 추가
                sql = """
                SELECT reference_date, name, closing_price, percentage_change, transaction_amount
                FROM market_price_change
                WHERE reference_date = '{}'
                order by percentage_change desc
                LIMIT {}, {}
                """.format(date, start_idx, items_per_page)

                print(sql)

                cursor.execute(sql)
                results = cursor.fetchall()
                print(results)
        
        except Exception as e:
            logging.error(f"Error : {e}")
        
        return jsonify({"results": results, "total_items": total_items, "items_per_page": items_per_page}) 
    else:
        # Render form template
        return render_template('theme.html')

@app.route('/wmb', methods=['GET','POST'])
def wmb():
    if request.method == 'POST':
        # Get form data
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        sort_by = request.form['sort_by']
        
        # Parse dates
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        print(f'start_date {start_date}, end_date {end_date}')
        
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        total_pages=0
        total_count=0
        results = []
        
        
        try:
            with conn.cursor() as cursor:
                count_sql = f"SELECT COUNT(*) as count FROM stock_issues " \
                            f"where report_time BETWEEN '{start_date}' and '{end_date}'"
                cursor.execute(count_sql)
                total_count = cursor.fetchone()['count']
                print(f'total_count: {total_count}')
        
                # Get data for the current page
                offset = (page - 1) * size
        
                sql = f"SELECT report_time, title, stock_name, news_content, news_link FROM stock_issues " \
                      f"where report_time BETWEEN '{start_date}' and '{end_date}' "\
                      f"order by report_time {sort_by} "\
                      f"LIMIT {size} OFFSET {offset}"
                cursor.execute(sql)
                results = cursor.fetchall()
                # print(results)
        
            # Calculate total number of pages
            total_pages = (total_count + size - 1) // size
            print(f'total_pages: {total_pages}')
        
            if results:
                return render_template('wmbresults.html', results=results)
            else:
                message = "검색 결과가 없습니다."
                return render_template('wmbresults.html', message=message)
        except Exception as e:
            logging.error(f"Error : {e}")
        
        return render_template('wmbresults.html', results=results, page=page, size=size, total_pages=total_pages, start_date=start_date, end_date=end_date)
    else:
        # Render form template
        return render_template('wmb.html')

def convert_none_to_null(value):
    return "''" if value is None else value


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
