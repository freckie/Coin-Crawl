import os
import sys
import time
import json
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
channel_list = ''
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
    for id in channel_list:
        try:
            bot.sendMessage(chat_id=id, text=msg)
            logger.info("Telegram Message Sent!")
            sleep(msg_timer)
        except Exception as exc:
            logger.info("[ERROR] Telegram Message sending error, error : " + str(exc))


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
    logger.info("UpBit start.")
    driver.get("https://upbit.com/exchange?")
    sleep(5)

    # 파일에 이전 데이터 읽어오기
    avail = _get_upbit_avail()
    now_list_u = []
    now_list_u.clear()

    try:
        bs = BeautifulSoup(driver.page_source, "lxml")
        div = bs.find("section", class_="ty02").find("div", class_="scrollB").find("table")
        trs = div.find_all("tr")
        for tr in trs:
            name = tr.find('td', class_='tit').find('a').get_text().strip()
            short = tr.find('td', class_='tit').find('em').get_text().strip()
            now_list_u.append(short)

            # 새로운 데이터라면
            if short not in avail:
                # 초기화 중이 아니라면
                if upbit_init:
                    msg = name + " (" + short + ") 상장."
                    _message(bot, "UpBit", msg)
                    avail.append(short)
                else:
                    avail.append(short)

        driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/section[2]/article[1]/span[2]/ul/li[2]/a').click()

        sleep(5)

        bs = BeautifulSoup(driver.page_source, "lxml")
        div = bs.find("section", class_="ty02").find("div", class_="scrollB").find("table")
        trs = div.find_all("tr")
        for tr in trs:
            name = tr.find('td', class_='tit').find('a').get_text().strip()
            short = tr.find('td', class_='tit').find('em').get_text().strip()
            now_list_u.append(short)

            # 새로운 데이터라면
            if short not in avail:
                # 초기화 중이 아니라면
                if upbit_init:
                    msg = name + " (" + short + ") 상장."
                    _message(bot, "UpBit", msg)
                    avail.append(short)
                else:
                    avail.append(short)

        sleep(5)

    except TimeoutException:
        logger.info("[ERROR] Loading took too much time!")

    # 파일에 데이터 저장
    _print_upbit_avail(avail)
    return True

'''
    # 폐장된 데이터 확인
    del_data = list(set(upbit_avail).difference(set(now_list_u)))
    for iter in del_data:
        msg = iter + " 거래소에서 제외됨 (폐장)."
        _message(bot, "UpBit", msg)
        upbit_avail.remove(str(iter))'''


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
    logger.info("Binance start.")
    
    # 파일에 이전 데이터 가져오기
    _binance_avail = _get_binance_avail()
    now_list = []

    # ID를 가져오기 위한 json parsing
    headers = {"Content-Type": "application/json; charset=utf-8"}
    url = "https://www.binance.com/exchange/public/product"
    json_string = str(BeautifulSoup(requests.get(url, headers=headers).text, 'lxml').find("p").getText())
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
    return True


if __name__ == "__main__":
    if os.path.exists("upbit_coins.dat"):
        os.remove('upbit_coins.dat')
    if os.path.exists("binance_coins.dat"):
        os.remove('binance_coins.dat')

    file_name = "./notice_setting.ini"
    driver_location = "./chromedriver.exe"

    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        driver_location = sys.argv[2]

    # 설정 데이터 읽기
    file = open(file_name, 'r')
    lines = file.readlines()

    driver_location = lines[1].replace("\n", "")
    my_token = lines[3].replace("\n", "")
    channel_id = lines[5].replace("\n", "")
    channel_list = channel_id.split(" ")
    delay_timer = int(lines[7].replace("\n", ""))
    msg_format = lines[9]
    start_timer = int(lines[11].replace("\n", ""))
    msg_timer = float(lines[13].replace("\n", ""))
    program_mode = lines[15].replace("\n", "")
    file.close()

    # Logger 초기화
    fileMaxByte = 1024 * 1024 * 100  # 100MB
    logger = logging.getLogger('coin')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    #fileHandler = logging.FileHandler('./coin.log')
    fileHandler = logging.handlers.RotatingFileHandler('./coin.log', maxBytes=fileMaxByte, backupCount=10)
    streamHandler = logging.StreamHandler()
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

    # 설정 출력
    logger.info("Ini file Location : " + file_name)
    logger.info("Driver Location : " + driver_location)
    logger.info("Telegram Bot Token : " + my_token)
    logger.info("Telegram Channel ID : " + channel_id)
    logger.info("Start Timer : " + str(start_timer))
    logger.info("Delay Timer : " + str(delay_timer))
    logger.info("초기 구성 완료.")

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
    logger.info("페이지 준비 완료. ")
    logger.info("프로세스 시작. ")
    started_time = time.time()
    while True:
        # 86400(24시간) - 180(3분) 이 지나면 프로그램 종료
        passed_time = time.time() - started_time
        if passed_time > 86220:
            logger.info("프로그램 실행 23시간 57분 경과. 프로그램이 3초 후 종료됩니다.")
            sleep(3)
            sys.exit(1)

        try:
            upbit_init = coins_upbit(driver, my_bot, upbit_init)
            sleep(delay_timer)
            binance_init = coins_binance(my_bot, binance_init)
            sleep(delay_timer)
        except Exception as exc:
            logger.info("[ERROR] " + str(exc))
