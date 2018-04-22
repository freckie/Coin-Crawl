from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from time import sleep
import time
import json
import telegram
from datetime import datetime
import logging.handlers
from selenium.webdriver.remote.remote_connection import LOGGER
import sys

# 전역변수
my_token = ''
channel_list = ''
already_checked = {'bithumb': '', 'upbit': '', 'binance1': '', 'binance2': ''} # 이미 체크한 공지들
driver_location = ""
word_upbit = []
word_bithumb = []
word_binance = []
delay_timer = 10
msg_format = ""
start_timer = 15


def message(bot, site, title, link):
    msg = msg_format.replace("$title", title).replace("$link", link).replace("$site", site).replace("%enter", "\n")
    try:
        for id in channel_list:
            bot.sendMessage(chat_id=id, text=msg)
        logger.info("Telegram Message Sent!")
    except Exception as exc:
        logger.info("[ERROR] Telegram Message sending error, error : " + str(exc))



# [디버깅용] 현재 시간 스트링으로 리턴
def _get_time():
    now = datetime.now()
    return str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)


# 문자열에 word_list가 있는지 확인 (text:string, word_list:list<string>)
def _string_find(text, word_list):
    for word in word_list:
        if word in text:
            return True
    return False


def notice_bithumb(driver, words):
    try:
        logger.info("Bithumb Start.")

        url = "http://bithumb.cafe/notice"
        driver.get(url)
        html = driver.page_source
        bs = BeautifulSoup(html, 'lxml')
        #div = bs.select("div#primary-fullwidth")[0]
        div = bs.find("div", {"id": "primary-fullwidth"} )

        # 최근 post만 가져오기
        #post = div.find_all("article")[0].select("h3 > a")[0]
        post = div.find_all("article")[0].find("h3").find("a")

        # link, title 추출
        post_link = post.get("href")
        post_title = post.getText()

        # link로 들어가 단어 있는지 확인
        new_bs = BeautifulSoup(requests.get(post_link).text, 'lxml')
        #article = new_bs.select("div.entry-content")[0]
        article = new_bs.find("div", class_="entry-content")
        spans = article.find_all("span")

        result = False
        for span in spans:
            result = _string_find(span.getText(), words)
            if result:
                break

    except AttributeError:
        logger.info("Bithumb not found.")
        return ("", "", False)

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def notice_upbit(driver, words):
    try:
        logger.info("UpBit Start.")

        # ID를 가져오기 위한 json parsing
        headers = {"Content-Type": "application/json; charset=utf-8"}
        url = "https://api-manager.upbit.com/api/v1/notices?page=1"
        html_code = BeautifulSoup(requests.get(url, headers=headers).text, 'lxml')
        json_string = html_code.find("p").getText()
        json_dict = json.loads(json_string)

        post_id = json_dict["data"]["list"][0]["id"]
        post_title = json_dict["data"]["list"][0]["title"]
        post_link = "https://www.upbit.com/service_center/notice?id=" + str(post_id)

        # 링크 들어가서 데이터 가져오기
        driver.get(post_link)
        html = driver.page_source
        sleep(2)
        bs = BeautifulSoup(html, 'lxml')
        #article = bs.select("div#markdown_notice_body")[0]
        article = bs.find("div", {"id": "markdown_notice_body"})
        p_tags = article.find_all("p")

        # 단어 확인
        result = False
        for p_tag in p_tags:
            result = _string_find(p_tag.getText(), words)
            if result:
                break

    except AttributeError:
        logger.info("UpBit not found.")
        return ("", "", False)

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def notice_binance(driver, words):
    try:
        logger.info("Binance Start.")

        url = "https://support.binance.com/hc/en-us/sections/115000202591-Latest-News"
        driver.get(url)
        html = driver.page_source
        bs = BeautifulSoup(html, 'lxml')
        #div = bs.select("ul.article-list")[0]
        div = bs.find("ul", class_='article-list')

        # 최근 post만 가져오기
        #post = div.find_all("li")[0].select("a")[0]
        post = div.find_all("li")[0].find("a")

        # link, title 추출
        post_link = "https://support.binance.com" + post.get("href")
        post_title = post.getText()

        # link로 들어가 단어 있는지 확인
        new_bs = BeautifulSoup(requests.get(post_link).text, 'lxml')
        #article = new_bs.select("div.article-body")[0]
        article = new_bs.find("div", class_="article-body")
        spans = article.find_all("span")

        result = False
        for span in spans:
            result = _string_find(span.getText(), words)
            if result:
                break

    except AttributeError:
        logger.info("Binance not found.")
        return ("", "", False)

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def notice_binance2(driver, words):
    try:
        logger.info("Binance_NewListings Start.")

        url = "https://support.binance.com/hc/en-us/sections/115000106672-New-Listings"
        driver.get(url)
        html = driver.page_source
        bs = BeautifulSoup(html, 'lxml')
        div = bs.find("ul", class_='article-list')

        # 최근 post만 가져오기
        post = div.find_all("li")[0].find("a")

        # link, title 추출
        post_link = "https://support.binance.com" + post.get("href")
        post_title = post.getText()

        # link로 들어가 단어 있는지 확인
        new_bs = BeautifulSoup(requests.get(post_link).text, 'lxml')
        article = new_bs.find("div", class_="article-body")
        spans = article.find_all("span")

        result = False
        for span in spans:
            result = _string_find(span.getText(), words)
            if result:
                break

    except AttributeError:
        logger.info("Binance_NewListings not found.")
        return ("", "", False)

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def loop(driver, bot, timer, words1, words2, words3):
    started_time = time.time()

    notice_init = False

    url = "https://www.upbit.com/service_center/notice"
    driver.get(url)
    logger.info("UpBit 브라우저 체킹 기다리는 중. (" + str(start_timer) + "sec 예정)")
    sleep(start_timer)
    logger.info("프로세스 시작.")

    while True:
        try:
            # 86400(24시간) - 180(3분) 이 지나면 프로그램 종료
            passed_time = time.time() - started_time
            if passed_time > 86220:
                logger.info("프로그램이 3초 후 종료됩니다.")
                sleep(3)
                sys.exit(1)

            data = notice_upbit(driver, words1)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['upbit'] == data[0]:
                    # 초기화된 상태일 때
                    if notice_init:
                        message(bot, "UpBit", data[0], data[1])
                    already_checked['upbit'] = data[0]
            sleep(timer)

            data = notice_bithumb(driver, words2)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['bithumb'] == data[0]:
                    # 초기화된 상태일 때
                    if notice_init:
                        message(bot, "Bithumb", data[0], data[1])
                    already_checked['bithumb'] = data[0]
            sleep(timer)

            data = notice_binance(driver, words3)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['binance'] == data[0]:
                    # 초기화된 상태일 때
                    if notice_init:
                        message(bot, "Binance", data[0], data[1])
                    already_checked['binance'] = data[0]
            sleep(timer)

            data = notice_binance2(driver, words3)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['binance2'] == data[0]:
                    # 초기화된 상태일 때
                    if notice_init:
                        message(bot, "Binance", data[0], data[1])
                    already_checked['binance2'] = data[0]
            sleep(timer)

            notice_init = True

        except Exception as exc:
            logger.info("[ERROR] loop unknown error." + str(exc))


if __name__ == "__main__":
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
    word_upbit = lines[7].replace("\n", "").split(" ")
    word_bithumb = lines[9].replace("\n", "").split(" ")
    word_binance = lines[11].replace("\n", "").split(" ")
    delay_timer = int(lines[13].replace("\n", ""))
    msg_format = lines[15]
    start_timer = int(lines[17].replace("\n", ""))

    file.close()

    # Logger 초기화
    fileMaxByte = 1024 * 1024 * 100  # 100MB
    logger = logging.getLogger('coin')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    fileHandler = logging.handlers.RotatingFileHandler('./notice.log', maxBytes=fileMaxByte, backupCount=10)
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
    driver = webdriver.Chrome(driver_location)
    LOGGER.setLevel(logging.CRITICAL)
    my_bot = telegram.Bot(token=my_token)
    driver.set_window_size(0, 0)
    logger.info("페이지 준비 완료. ")

    # 프로그램 시작
    loop(driver, my_bot, delay_timer, word_upbit, word_bithumb, word_binance)