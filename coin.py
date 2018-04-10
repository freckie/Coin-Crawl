import os
import json
import logging
import requests
import telegram
import logging.handlers

from time import sleep
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.remote_connection import LOGGER

my_token = ''
channel_id = ''
driver_location = ""
delay_timer = 10
msg_format = ""
start_timer = 15
msg_timer = 0.5


# [디버깅용] 현재 시간 스트링으로 리턴
def _get_time():
    now = datetime.now()
    return str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)


def _message(bot, site, message):
    msg = msg_format.replace("$message", message).replace("$site", site).replace("%enter", "\n")
    try:
        bot.sendMessage(chat_id=channel_id, text=msg)
        logger.info("[SYSTEM] Telegram Message 전송 완료!")
        sleep(msg_timer)
    except:
        logger.info("[ERROR] Telegram Message 전송 실패!")


def _get_upbit_avail():
    upbit_avail = []
    # 데이터 읽기
    try:
        file = open("upbit_coins.dat", 'r', encoding="utf-8-sig")
    except FileNotFoundError:
        return upbit_avail

    data_list = file.read().split(" ")
    for data in data_list:
        upbit_avail.append(data)
    file.close()

    return upbit_avail


def _print_upbit_avail(upbit_avail):
    if os.path.exists("upbit_coins.dat"):
        os.remove('upbit_coins.dat')

    # 데이터 쓰기
    file2 = open("upbit_coins.dat", "w", encoding="utf-8")
    for data in upbit_avail:
        if data == upbit_avail[-1]:
            file2.write(data)
        else:
            file2.write(data + " ")
    file2.close()

    return True


def coins_upbit(driver, bot, upbit_init):
    logging.info("[SYSTEM] UpBit 진행 시작.")
    driver.refresh()
    sleep(5)

    # 파일에 이전 데이터 읽어오기
    upbit_avail = _get_upbit_avail()
    now_list_u = []
    now_list_u.clear()

    try:
        logging.info("[SYSTEM] UpBit 에서 KRW 기반 크롤링 시작.")
        bs = BeautifulSoup(driver.page_source, "html.parser")
        div = bs.find("section", class_="ty02").find("div", class_="scrollB").find("table")
        trs = div.find_all("tr")
        for tr in trs:
            name = tr.find('td', class_='tit').find('a').get_text().strip()
            short = tr.find('td', class_='tit').find('em').get_text().strip()
            temp = {
                'name': name,
                'symbol': short,
            }
            # 새로운 데이터라면
            if temp['symbol'] not in upbit_avail:
                # 초기화 중이 아니라면
                if upbit_init:
                    msg = temp['name'] + " (" + temp['symbol'] + ") 상장."
                    _message(bot, "UpBit", msg)
                    upbit_avail.append(temp['symbol'])
                else:
                    upbit_avail.append(temp['symbol'])
            now_list_u.append(temp['symbol'])

        logging.info("[SYSTEM] UpBit 에서 KRW 기반 크롤링 완료.")
        
        driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/section[2]/article[1]/span[2]/ul/li[2]/a').click()

        sleep(5)

        logging.info("[SYSTEM] UpBit 에서 BTC 기반 크롤링 시작.")
        bs = BeautifulSoup(driver.page_source, "html.parser")
        div = bs.find("section", class_="ty02").find("div", class_="scrollB").find("table")
        trs = div.find_all("tr")
        for tr in trs:
            name = tr.find('td', class_='tit').find('a').get_text().strip()
            short = tr.find('td', class_='tit').find('em').get_text().strip()
            temp = {
                'name': name,
                'symbol': short
            }
            # 새로운 데이터라면
            if temp['symbol'] not in upbit_avail:
                # 초기화 중이 아니라면
                if upbit_init:
                    msg = temp['name'] + " (" + temp['symbol'] + ") 상장."
                    _message(bot, "UpBit", msg)
                    upbit_avail.append(temp['symbol'])
                else:
                    upbit_avail.append(temp['symbol'])
            now_list_u.append(temp['symbol'])
        logging.info("[SYSTEM] UpBit 에서 BTC 기반 크롤링 완료.")
        sleep(5)

    except TimeoutException:
        logging.info("[ERROR] Loading took too much time!")
    except Exception as exc:
        logging.info("[ERROR] " + str(exc) + "error.")

    # 폐장된 데이터 확인
    del_data = list(set(upbit_avail).difference(set(now_list_u)))
    for iter in del_data:
        msg = iter + " 거래소에서 제외됨 (폐장)."
        _message(bot, "UpBit", msg)
        upbit_avail.remove(str(iter))

    # 파일에 데이터 저장
    _print_upbit_avail(upbit_avail)
    logging.info("[SYSTEM] UpBit 진행 완료.")
    return True


def _get_binance_avail():
    binance_avail = list()
    # 데이터 읽기
    try:
        file = open("binance_coins.dat", 'r')
    except FileNotFoundError:
        return binance_avail

    data_list = file.readlines()
    for data in data_list:
        temp = data.replace("\n", "")
        binance_avail.append(temp)

    file.close()

    return binance_avail


def _print_binance_avail(binance_avail):
    # 파일 존재하면 삭제하고
    if os.path.exists("binance_coins.dat"):
        os.remove('binance_coins.dat')

    # 데이터 쓰기
    file = open("binance_coins.dat", "w", encoding="utf-8")
    for item in binance_avail:
        file.write(item + "\n")
    file.close()

    return True


def coins_binance(bot, _binance_init):
    logging.info("[SYSTEM] Binance 진행 시작.")
    
    # 파일에 이전 데이터 가져오기
    _binance_avail = _get_binance_avail()
    now_list = []

    # ID를 가져오기 위한 json parsing
    headers = {"Content-Type": "application/json; charset=utf-8"}
    url = "https://www.binance.com/exchange/public/product"
    json_string = str(BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser'))
    json_data = json.loads(json_string)['data']

    for data in json_data:
        temp = {
            "symbol": data['symbol'],
            "quote": data['quoteAssetName'].replace(" ", "_"),
            "base": data['baseAssetName'].replace(" ", "_")
        }
        # 초기 구성 중이라면
        if not _binance_init:
            _binance_avail.append(temp['symbol'])
            now_list.append(temp['symbol'])
        # 초기 구성 완료된 상태라면
        else:
            # 새로운 데이터
            if temp['symbol'] not in _binance_avail:
                msg = temp['symbol'] + "(" + temp['quote'] + " - " + temp['base'] + ") 거래 가능. (상장)"
                _message(bot, "Binance", msg)
                _binance_avail.append(temp['symbol'])

        now_list.append(temp['symbol'])

    # 폐장된 데이터 확인
    del_data = list(set(_binance_avail).difference(set(now_list)))
    for iter in del_data:
        msg = iter + " 거래소에서 제외됨 (폐장)."
        _message(bot, "Binance", msg)
        _binance_avail.remove(str(iter))

    _print_binance_avail(_binance_avail)
    logging.info("[SYSTEM] Binance 진행 완료.")
    return True


if __name__ == "__main__":
    if os.path.exists("upbit_coins.dat"):
        os.remove('upbit_coins.dat')
    if os.path.exists("binance_coins.dat"):
        os.remove('binance_coins.dat')

    # 설정 데이터 읽기
    file = open("coin_setting.ini", 'r')
    lines = file.readlines()

    driver_location = lines[1].replace("\n", "")
    my_token = lines[3].replace("\n", "")
    channel_id = lines[5].replace("\n", "")
    delay_timer = int(lines[7].replace("\n", ""))
    msg_format = lines[9]
    start_timer = int(lines[11].replace("\n", ""))
    msg_timer = float(lines[13].replace("\n", ""))
    program_mode = lines[15].replace("\n", "")
    file.close()

    # Logger 초기화
    logger = logging.getLogger('coin')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    fileHandler = logging.FileHandler('./coin.log')
    streamHandler = logging.StreamHandler()
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

    # 설정 출력
    logger.info("[SYSTEM] 페이지 준비 완료. ")
    logger.info("[SYSTEM] Telegram Bot Token : " + my_token)
    logger.info("[SYSTEM] Telegram Channel ID : " + channel_id)
    logger.info("[SYSTEM] Start Timer : " + str(start_timer))
    logger.info("[SYSTEM] Delay Timer : " + str(delay_timer))
    logger.info("[SYSTEM] 초기 구성 완료.")

    # 웹드라이버 및 봇 초기화
    my_bot = telegram.Bot(token=my_token)
    driver = webdriver.Chrome(driver_location)
    LOGGER.setLevel(logging.CRITICAL)
    driver.maximize_window()
    driver.get("https://upbit.com/exchange?")

    # 프로그램 시작
    upbit_avail = []
    binance_avail = []

    if program_mode == "Test":
        upbit_init = True
        binance_init = True
    else:
        upbit_init = False
        binance_init = False

    sleep(start_timer)
    logger.info("[SYSTEM] 페이지 준비 완료. ")
    logger.info("[SYSTEM] 프로세스 시작. ")
    while True:
        sleep(delay_timer)
        upbit_init = coins_upbit(driver, my_bot, upbit_init)
        sleep(delay_timer)
        binance_init = coins_binance(my_bot, binance_init)