import json
import requests
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver

# 전역변수
driver_location = "./chromedriver.exe"
upbit_avail = []


def _get_upbit_avail():
    # 데이터 읽기
    file = open("upbit_coins.dat", 'r')
    data_list = file.read().split(" ")
    for data in data_list:
        upbit_avail.append(data)
    file.close()


def _print_upbit_avail():
    # 데이터 쓰기
    file = open("upbit_coins.dat", "w")
    for data in upbit_avail:
        file.write(data + " ")
    file.close()


def _message(bot, site, title, link):
    #msg = msg_format.replace("$title", title).replace("$link", link).replace("$site", site).replace("%enter", "\n")
    #bot.sendMessage(chat_id=channel_id, text=msg)
    print("[SYSTEM] Telegram Message 전송 완료. (새로운 코인 상장됨.)")


def coins_upbit(driver):
    url = "https://www.upbit.com/trends"
    driver.get(url)
    driver.find_element_by_xpath('//*[@id="root"]/div/div/div[3]/section[1]/article[2]/a').click()

    # 버튼 클릭된 이후의 table 크롤링
    html = driver.page_source
    bs = BeautifulSoup(html, 'html.parser')
    table = bs.select("table.ty03")[1].find("tbody")
    tr_tags = table.find_all("tr")

    # 버튼이 있는 코인 이름들만 리스트에 추가
    for tr_tag in tr_tags:
        name = tr_tag.select("a.tit > strong")[0].getText()
        btn_txt = tr_tag.select("td.btn")[0].getText()

        if btn_txt == "거래하기":
            if name not in upbit_avail:
                print("새로운거다!!!")
                upbit_avail.append(name)
                _print_upbit_avail()


if __name__ == "__main__":
    driver = webdriver.Chrome(driver_location)
    driver.get("https://www.upbit.com/trends")
    sleep(10)
    coins_upbit(driver)