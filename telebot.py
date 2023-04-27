import re
import asyncio
import sys
import traceback
import json

import pytz
from telethon import TelegramClient
from datetime import datetime, timedelta
from config.db_handle import *
import logging


logging.basicConfig(filename='log/telebot.log', 
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s')

# Load the config file
with open('config/config.json') as f:
    config = json.load(f)

api_id = config["api_id"]
api_hash = config["api_hash"]
session_name = config["session_name"]

# 텔레그램 클라이언트 인스턴스 생성
client = TelegramClient(session_name, api_id, api_hash)


async def get_messages(channel_name):
    # 채널 정보 가져오기
    channel_entity = await client.get_entity(channel_name)
    channel_id = channel_entity.id

    messages = []
    # messages = await client.get_messages(channel_id, limit=message_count)
    async for message in client.iter_messages(channel_id):
        kst_datetime = datetime.fromtimestamp(message.date.timestamp(), tz=kst_timezone)
        kst_time = kst_datetime.strftime("%Y-%m-%d %H:%M:%S")
        messages.append((kst_time, message.text))
        if kst_datetime.timestamp() < start_date.timestamp():
            break;
    return messages

def check_duplication(con, seen):
    rows = execute_query(con,"SELECT report_time, title, stock_name FROM stock_issues")
    for row in rows:
        title = row['title'].replace("'", "''") if row['title'] else ""
        stock_name = row['stock_name'].replace("'", "''") if row['stock_name'] else ""
        seen.add((row['report_time'].strftime('%Y-%m-%d %H:%M:%S'), title, stock_name ))

    logging.debug(f"seen set: {seen}")

    return seen


async def bot_main(con, chn_list):
    await client.start()
    for chn in chn_list:
        messages = await get_messages(chn)
        # print(f' messages : {messages}')
        message_list = []
        seen = set()
        title = ""
        seen = check_duplication(con, seen)

        for date, message in messages:

            #date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

            if chn == "wemakebull" and message:
                title, name, contents, link = extract_wmb_msg(message)
                # 키값을 날짜, 제목, 종목명
                key = (date,title,name)
                logging.debug(f'key - {key}')


            # 중복체크
            if title and name and key not in seen:
                message_list.append((date, title, name, contents, link, chn))
                seen.add(key)
                logging.debug(f'not duplicated - 날짜 : {date} , 타이틀 : {title}, 종목명 : {name}, 이슈내용 : {contents}, 링크 : {link}, 채널명 : {chn}')

        if message_list:
            # print(f'news_list : {message_list}')
            values = ','.join(
                map(lambda x: f"('{x[0]}', '{x[1]}', '{x[2]}', '{x[3]}', '{x[4]}', '{x[5]}')", message_list))
            sql = f"INSERT INTO stock_issues (report_time, title, stock_name, news_content, news_link, channel_name) " \
                  f"VALUES {values}"
            print(f'insert query {sql}')
            execute_insert_query(con, sql)
    await client.disconnect()


def extract_wmb_msg(messages):
    """
    :param messages:
    :return:
    """

    issue_content = ""
    # 이슈 타이틀 추출
    try:
        lines = messages.split('\n')
        #logging.info(f'message line : {messages}')
        if '🎉' in lines[0]:
            return None, None, None, None

        # 첫줄에 Comments 란 단어가 있을때
        name = []
        issue_content = ''
        if 'Comments' in lines[0]:
            title = lines[0].replace('**', '')
        elif '✅' in lines[0] or '✅' in lines[0]:
            title = lines[0]
            title = title.replace('*', '')
        elif match := re.search(r"^\*\*\[\S+:\s*(.*?)\]", lines[0]):
            title = match.group(0)
            title = title.replace('*', '')
        elif match := re.search(r'\[([^\]]+)\]', lines[0]):
            title = lines[0].replace('*', '')
        elif '▶️' in lines[0]:
            title = lines[0]
        else:
            title = ""

        name_list = re.findall(r"\[(.*?)\]", lines[0])
        for n in name_list:
            if n not in name:
                if ':' in n:
                    n = n.split(':')[1].strip()
                    name.append(n)
                else:
                    name.append(n)
        for idx, line in enumerate(lines[1:]):
            if '✅' in line or '✅' in line or '▶️' in line:
                if idx == 0:
                    title = line.strip()
                else:
                    issue_content += line.strip().replace('*', '') + "\n"
#                name_list = re.findall(r"\[(.*?)\]", line)
#                for n in name_list:
#                    if n not in name:
#                        name.append(n)
        # 링크 추출
        # link = re.findall(r"(https?://\S+)", messages)
        # link = re.findall(r'https?://[^\s]+', messages)
        link = re.findall(r"(https?://[^\s()]+(?:\([\w\d]+\)|[^\s()]))", messages)

        title = title.replace("'", "''") if title else ""
        name = ','.join(name).replace("'", "''") if name else ""
        contents = issue_content.replace("'", "''").replace("‘", "''")
        link = ' '.join(link).replace("'", "''")
        # link = re.sub(r'\)', '', link).re.sub(r'*', '', link).re.sub(r'▶️', '', link)

        # print(f"이슈타이틀: {title}, 종목명 : {name}, 컨텐츠 : {contents}, 링크 : {link}")

        # 타이틀,종목명,내용,링크
        return title, name, contents, link

    except Exception as e:
        tb = traceback.format_exc()
        logging.error(f"Error occurred at line {sys.exc_info()[-1].tb_lineno}: {e}\n{tb}")
        return None, None, None, None


def extract_cts_msg(message):
    pattern = r"\[특징주\]\s*(.*?),\s*(.*?)\n(https?://\S+)"
    # pattern = r"\[특징주\]\s*(.*?),\s*(.*?)(\n(http\S+))?"
    match = re.search(pattern, message)

    if match:
        stock_name = match.group(1)
        title = match.group(2)
        link = match.group(3) if match.group(3) else None
        logging.info(f'타이틀 :{title}, 종목명 :{stock_name}, 링크 : {link}')
        # 종목명,내용,링크
        stock_name = stock_name.replace("'", "''")
        title = title.replace("'", "''")

        return title, stock_name, link
    else:
        return None


if __name__ == '__main__':
    # 검색기간
    kst_timezone = pytz.timezone('Asia/Seoul')
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
    # message_count = 60

    # MySQL 연결 설정
    conn = connect_db()

    channel1 = config['channel_name1']
#    channel2 = config['channel_name2']

    # channel_list = [channel1, channel2]
    channel_list = [channel1]

    asyncio.run(bot_main(conn, channel_list))
