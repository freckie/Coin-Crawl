from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from time import sleep
import json
import telegram

# 전역변수
my_token = ''
channel_id = ''
already_checked = {'bithumb':'', 'upbit':'', 'binance':''} # 이미 체크한 공지들
driver_location = ""
word_upbit = []
word_bithumb = []
word_binance = []
delay_timer = 10
msg_format = ""
start_timer = 15


# 문자열에 word_list가 있는지 확인 (text:string, word_list:list<string>)
def _string_find(text, word_list):
    for word in word_list:
        if word in text:
            return True
    return False


def notice_bithumb(driver, words):
    url = "http://bithumb.cafe/notice"
    driver.get(url)
    html = driver.page_source
    bs = BeautifulSoup(html, 'html.parser')
    div = bs.select("div#primary-fullwidth")[0]

    # 최근 post만 가져오기
    post = div.find_all("article")[0].select("h3 > a")[0]

    # link, title 추출
    post_link = post.get("href")
    post_title = post.getText()

    # link로 들어가 단어 있는지 확인
    new_bs = BeautifulSoup(requests.get(post_link).text, 'html.parser')
    article = new_bs.select("div.entry-content")[0]
    spans = article.find_all("span")

    result = False
    for span in spans:
        result = _string_find(span.getText(), words)
        if result:
            break

    #print("[SYSTEM] bithumb 진행.")

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def notice_upbit(driver, words):
    # ID를 가져오기 위한 json parsing
    headers = {"Content-Type":"application/json; charset=utf-8"}
    url = "https://api-manager.upbit.com/api/v1/notices?page=1"
    json_string = str(BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser'))
    json_dict = json.loads(json_string)

    post_id = json_dict["data"]["list"][0]["id"]
    post_title = json_dict["data"]["list"][0]["title"]
    post_link = "https://www.upbit.com/service_center/notice?id=" + str(post_id)

    # 링크 들어가서 데이터 가져오기
    driver.get(post_link)
    html = driver.page_source
    bs = BeautifulSoup(html, 'html.parser')
    article = bs.select("div#markdown_notice_body")[0]
    p_tags = article.find_all("p")

    # 단어 확인
    result = False
    for p_tag in p_tags:
        result = _string_find(p_tag.getText(), words)
        if result:
            break

    #print("[SYSTEM] upbit 진행.")

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def notice_binance(driver, words):
    url = "https://support.binance.com/hc/en-us/sections/115000202591-Latest-News"
    driver.get(url)
    html = driver.page_source
    bs = BeautifulSoup(html, 'html.parser')
    div = bs.select("ul.article-list")[0]

    # 최근 post만 가져오기
    post = div.find_all("li")[0].select("a")[0]

    # link, title 추출
    post_link = "https://support.binance.com" + post.get("href")
    post_title = post.getText()

    # link로 들어가 단어 있는지 확인
    new_bs = BeautifulSoup(requests.get(post_link).text, 'html.parser')
    article = new_bs.select("div.article-body")[0]
    spans = article.find_all("span")

    result = False
    for span in spans:
        result = _string_find(span.getText(), words)
        if result:
            break

    # console
    #print("[SYSTEM] binance 진행.")

    # 리턴용 데이터 (제목, 링크, 단어검색성공여부)
    return (post_title, post_link, result)


def message(bot, site, title, link):
    msg = msg_format.replace("$title", title).replace("$link", link).replace("$site", site).replace("%enter", "\n")
    bot.sendMessage(chat_id=channel_id, text=msg)
    #print("[SYSTEM] Telegram Message 전송 완료. (키워드 발견함.)")


def loop(driver, bot, timer, words1, words2, words3):
    url = "https://www.upbit.com/service_center/notice"
    driver.get(url)
    print("[SYSTEM] upbit 브라우저 체킹 기다리는 중. (" + str(start_timer) + "sec 예정)")
    sleep(start_timer)
    print("[SYSTEM] 프로세스 시작.")

    while True:
        print("")
        try:
            data = notice_upbit(driver, words1)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['upbit'] == data[0]:
                    already_checked['upbit'] = data[0]
                    message(bot, "upbit", data[0], data[1])
            sleep(timer)

            data = notice_bithumb(driver, words2)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['bithumb'] == data[0]:
                    already_checked['bithumb'] = data[0]
                    message(bot, "bithumb", data[0], data[1])
            sleep(timer)

            data = notice_binance(driver, words3)
            # 단어 검색되었을 때
            if data[2]:
                # 이미 검색한 것이 아닐 때
                if not already_checked['binance'] == data[0]:
                    already_checked['binance'] = data[0]
                    message(bot, "binance", data[0], data[1])
            sleep(timer)

        except:
            print("Error.")
            continue


if __name__ == "__main__":
    # 설정 데이터 읽기
    file = open("notice_setting.ini", 'r')
    lines = file.readlines()

    driver_location = lines[1].replace("\n", "")
    my_token = lines[3].replace("\n", "")
    channel_id = lines[5].replace("\n", "")
    word_upbit = lines[7].replace("\n", "").split(" ")
    word_bithumb = lines[9].replace("\n", "").split(" ")
    word_binance = lines[11].replace("\n", "").split(" ")
    delay_timer = int(lines[13].replace("\n", ""))
    msg_format = lines[15]
    start_timer = int(lines[17].replace("\n", ""))

    file.close()

    # 설정 출력
    print("[SYSTEM] 초기 구성 완료.")
    print("[SYSTEM] Telegram Bot Token : " + my_token)
    print("[SYSTEM] Telegram Channel ID : " + channel_id)
    print("[SYSTEM] Start Timer : " + str(start_timer))
    print("[SYSTEM] Delay Timer : " + str(delay_timer))
    print("")

    # 웹드라이버 및 봇 초기화
    driver = webdriver.Chrome(driver_location)
    my_bot = telegram.Bot(token=my_token)

    # 프로그램 시작
    loop(driver, my_bot, delay_timer, word_upbit, word_bithumb, word_binance)