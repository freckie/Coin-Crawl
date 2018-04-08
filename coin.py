import json
import requests
import telegram
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver

my_token = ''
channel_id = ''
already_checked = {'bithumb':'', 'upbit':'', 'binance':''} # 이미 체크한 공지들
driver_location = ""
delay_timer = 10
msg_format = ""
start_timer = 15


def _message(bot, site, message):
    msg = msg_format.replace("$message", message).replace("$site", site).replace("%enter", "\n")
    bot.sendMessage(chat_id=channel_id, text=msg)
    print("[SYSTEM] Telegram Message 전송 완료.")


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
    # 데이터 쓰기
    file = open("upbit_coins.dat", "w", encoding="utf-8")
    for data in upbit_avail:
        if data == upbit_avail[-1]:
            file.write(data)
        else:
            file.write(data + " ")
    file.close()

    return True


def coins_upbit(driver, bot, upbit_init):
    url = "https://www.upbit.com/trends"
    driver.get(url)
    driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/section[1]/article[2]/a').click()

    # 버튼 클릭된 이후의 table 크롤링
    html = driver.page_source
    bs = BeautifulSoup(html, 'html.parser')
    table = bs.select("table.ty03")[1].find("tbody")
    tr_tags = table.find_all("tr")

    # 파일에 이전 데이터 읽어오기
    upbit_avail = _get_upbit_avail()

    idx = 1
    # 버튼이 있는 코인 이름들만 리스트에 추가
    for tr_tag in tr_tags:
        name = tr_tag.select("a.tit > strong")[0].getText()
        btn = tr_tag.select("a.btn03")

        # 새로 추가된 코인
        if btn:
            if name not in upbit_avail:
                if upbit_init:  # 초기데이터 저장된 상태라면
                    _message(bot, "upbit", name + " 상장.")
                    upbit_avail.append(name)
                else:
                    upbit_avail.append(name)
        # 없어진 코인
        else:
            if name in upbit_avail:
                if name == "퀀텀":
                    continue
                _message(bot, "upbit", name + " 폐장.")
                upbit_avail.remove(name)
        idx+=1

    # 파일에 데이터 저장
    _print_upbit_avail(upbit_avail)
    return True


def _get_binance_avail():
    binance_avail = []
    # 데이터 읽기
    try:
        file = open("binance_coins.dat", 'r')
    except FileNotFoundError:
        return binance_avail

    data_list = file.readlines()
    for data in data_list:
        temp = data.replace("\n", "").split(" ")
        tmp_dict = {
            'symbol': temp[0],
            'quote': temp[1],
            'base': temp[2]
        }
        binance_avail.append(tmp_dict)

    file.close()

    return binance_avail


def _print_binance_avail(binance_avail):
    # 데이터 쓰기
    file = open("binance_coins.dat", "w", encoding="utf-8")
    for item in binance_avail:
        file.write(item['symbol'] + " " + item['quote'] + " " + item['base'] + "\n")
    file.close()

    return True


def coins_binance(bot, binance_init):
    # 파일에 이전 데이터 가져오기
    binance_avail = _get_binance_avail()
    symbol_list = []
    for item in binance_avail:
        symbol_list.append(item['symbol'])

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
        if not binance_init:
            binance_avail.append(temp)
        # 초기 구성 완료된 상태라면
        else:
            # 새로운 데이터
            if temp['symbol'] not in symbol_list:
                msg = temp['symbol'] + "(" + temp['quote'] + " - " + temp['base'] + ") 거래 가능."
                _message(bot, "binance", msg)
                binance_avail.append(temp)

    _print_binance_avail(binance_avail)
    return True


if __name__ == "__main__":
    # 설정 데이터 읽기
    file = open("coin_setting.ini", 'r')
    lines = file.readlines()

    driver_location = lines[1].replace("\n", "")
    my_token = lines[3].replace("\n", "")
    channel_id = lines[5].replace("\n", "")
    delay_timer = int(lines[7].replace("\n", ""))
    msg_format = lines[9]
    start_timer = int(lines[11].replace("\n", ""))
    program_mode = lines[13].replace("\n", "")

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
    driver.get("https://www.upbit.com/trends")
    my_bot = telegram.Bot(token=my_token)

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
    while True:
        upbit_init = coins_upbit(driver, my_bot, upbit_init)
        sleep(delay_timer)
        binance_init = coins_binance(my_bot, binance_init)
        sleep(delay_timer)