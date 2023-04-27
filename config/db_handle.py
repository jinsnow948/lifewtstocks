import os
import json
import pymysql

# Load the config file
with open('/home/jinwon/lifewtstocks/config/config.json') as f:
    config = json.load(f)

def connect_db():
    conn = pymysql.connect(
        host=config["MYSQL_HOST"],
        user=config["MYSQL_USER"],
        password=config["MYSQL_PASSWORD"],
        db=config["MYSQL_DB"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


def execute_query(conn, query, *args):
    with conn.cursor() as cursor:
        cursor.execute(query, args)
        result = cursor.fetchall()
    return result


def execute_insert_query(conn, query):
    with conn.cursor() as cursor:
        cursor.execute(query)
    conn.commit()


def drop_tables_stock_trading(conn):
    drop_table_query = """
    DROP TABLE IF EXISTS stock_trading;
    """
    execute_query(conn, drop_table_query)
    print(f"stock_trading table is DROPPED!")


def create_table_stock_trading(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS stock_trading (
        code varchar(20) NOT NULL,
        trading_date date NOT NULL,
        stock_name varchar(100) NOT NULL,
        foreign_total bigint DEFAULT NULL,
        institution bigint DEFAULT NULL,
        individual bigint DEFAULT NULL,
        agency_total bigint DEFAULT NULL,
        PRIMARY KEY (code,trading_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    execute_query(conn, create_table_query)


def drop_tables_stock_news(conn):
    drop_table_query = """
    DROP TABLE IF EXISTS stock_news;
    """
    execute_query(conn, drop_table_query)
    print(f"stock_news table is DROPPED!")


def create_table_stock_news(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS stock_news (
        code VARCHAR(20) NOT NULL,
        article_date date NOT NULL,
        title VARCHAR(100) NOT NULL,
        stock_name varchar(100) NOT NULL,
        link VARCHAR(200) NOT NULL,
        PRIMARY KEY (code, article_date, title)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    execute_query(conn, create_table_query)

def drop_tables_stock_issues(conn):
    drop_table_query = """
    DROP TABLE IF EXISTS stock_issues;
    """
    execute_query(conn, drop_table_query)
    print(f"stock_issues table is DROPPED!")
	
def create_table_stock_issues(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS stock_issues (
        report_time DATETIME NOT NULL,
        title VARCHAR(400) NOT NULL,
        stock_name VARCHAR(255) NOT NULL,        
        news_content TEXT,
        news_link VARCHAR(600),
        channel_name VARCHAR(255),
        PRIMARY KEY (report_time, title, stock_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    execute_query(conn, create_table_query)

def drop_market_price_change(conn):
    drop_table_query = """
    DROP TABLE IF EXISTS market_price_change;
    """
    execute_query(conn, drop_table_query)
    print(f"market_price_change table is DROPPED!")

def create_market_price_change(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS market_price_change (
                reference_date date,
		ticker VARCHAR(10) NOT NULL,
		name VARCHAR(50) NOT NULL,
		opening_price INT,
		closing_price INT,
		price_change INT,
		percentage_change DECIMAL(5, 2),
		volume INT,
		transaction_amount BIGINT,
		PRIMARY KEY (reference_date,ticker)
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
	"""
    execute_query(conn, create_table_query)

def drop_theme_info(conn):
    drop_table_query = """
    DROP TABLE IF EXISTS theme_info;
    """
    execute_query(conn, drop_table_query)
    print(f"theme_info table is DROPPED!")

def create_theme_info(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS theme_info (
          theme_name VARCHAR(255) NOT NULL,
          theme_detail_name VARCHAR(255) NOT NULL,
          related_stock_code VARCHAR(255) NOT NULL,
          related_stock_name VARCHAR(255) NOT NULL,
          theme_occurrence_date DATE NOT NULL,
          theme_description TEXT NOT NULL
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
	"""
    execute_query(conn, create_table_query)

def drop_stock_ticker(conn):
    drop_table_query = """
    DROP TABLE IF EXISTS stock_ticker;
    """
    execute_query(conn, drop_table_query)
    print(f"theme_info table is DROPPED!")

def create_stock_ticker(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS stock_ticker(
          stock_name VARCHAR(255) NOT NULL,
          ticker VARCHAR(255) NOT NULL,
          PRIMARY KEY (stock_name, ticker)
	)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
	"""
    execute_query(conn, create_table_query)
