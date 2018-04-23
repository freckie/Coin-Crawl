from __future__ import print_function

import os
import sys
import time
import logging
import telegram
import logging.handlers
from httplib2 import Http
import apiclient
from apiclient import errors
from oauth2client import file, client, tools

# 설정변수
file_dir = ""
my_token = ""
channel_list = []
word1 = []
word2 = []
word3 = []
word1_emoji = {}
word2_emoji = {}
word3_emoji = {}
delay_timer = 10
msg_format = ""


# emoji 연결하기
def _emoji_str(emoji_list):
    result = ""
    for emoji in emoji_list:
        result += eval("u'" + emoji + "'")
        result += " "
    return result


# data 읽기
def _get_data():
    msg_ids = []
    try:
        get_file = open(file_dir + "email_sorter.dat", 'r')
    except FileNotFoundError:
        return msg_ids

    msg_ids = get_file.read().split(" ")
    get_file.close()

    if '' in msg_ids:
        msg_ids.remove('')

    return msg_ids


# data 출력
def _print_data(msg_ids):
    if os.path.exists(file_dir + "email_sorter.dat"):
        os.remove(file_dir + 'email_sorter.dat')
    print_file = open(file_dir + 'email_sorter.dat', "w")

    if len(msg_ids) == 0:
        return True

    cnt = 1
    for msg_id in msg_ids:
        if cnt > 5:
            break
        if msg_id == msg_ids[-1]:
            print_file.write(msg_id)
        else:
            print_file.write(msg_id + " ")
        cnt += 1
    print_file.close()

    return True


# 메세징 함수
def _message(bot, ch_id, title):
    msg = msg_format.replace("$title", title).replace("%enter", '\n')
    try:
        bot.sendMessage(chat_id=ch_id, text=msg)
        logger.info("Message Sent!")
    except Exception as exc:
        logger.info("[ERROR] Telegram Messaging Fail! : " + str(exc))


# Email 데이터 파싱 및 메세징
def sorter(bot, data):
    title_str = data.replace("TradingView Alert: ", "")
    origin = str(title_str)     # 원본 메세지
    title_str = title_str.lower()

    try:
        for word in word1:
            if word.lower() in title_str:
                msg = origin + " " + _emoji_str(word1_emoji[word])
                _message(bot, channel_list[0], msg)
        for word in word2:
            if word.lower() in title_str:
                msg = origin + " " + _emoji_str(word2_emoji[word])
                _message(bot, channel_list[1], msg)
        for word in word3:
            if word.lower() in title_str:
                msg = origin + " " + _emoji_str(word3_emoji[word])
                _message(bot, channel_list[2], msg)
    except Exception as exc:
        logger.info("[ERROR] sorter() error : " + str(exc))


# 메세지 ID를 List로 가져옴.
def ListMessagesWithLables(service, user_id, label_ids=[]):
    try:
        response = service.users().messages().list(userId=user_id,
                                                   labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,
                                                       labelIds=label_ids,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        logger.info("[ERROR] GetMessageList error : " + str(error))


# 메세지 내용을 리턴.
def GetMessage(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        header_list = message['payload']['headers']
        for header in header_list:
            if header['name'] == 'Subject':
                return header['value']
    except errors.HttpError as error:
        logger.info('[ERROR] GetMessage error : ' + str(error))


# 프로그램 메인 함수
def loop(service, id, bot):
    init = False
    started_time = time.time()

    while True:
        try:
            logger.info("Processing...")

            # 데이터 읽어오기
            origin_list = _get_data()

            # 86400(24시간) - 180(3분) 이 지나면 프로그램 종료
            passed_time = time.time() - started_time
            if passed_time > 86220:
                logger.info("프로그램 진행 시간 : 23시간 57분. 프로그램이 3초 후 종료됩니다.")
                time.sleep(3)
                sys.exit(1)

            # 최근 메세지 확인.
            ids = ListMessagesWithLables(service=service, user_id=id)[0:5]
            for it in ids:
                # 새로운 메시지 ID
                if not (it['id'] in origin_list):
                    if init is False:
                        origin_list.append(it['id'])
                    else:
                        origin_list.insert(0, it['id'])
                        msg = GetMessage(service=service, user_id=id, msg_id=it['id'])
                        sorter(bot=bot, data=msg)

            init = True

            # 데이터 출력
            _print_data(origin_list)

            time.sleep(delay_timer)
        except Exception as exc:
            logger.info("[ERROR] loop() error : " + str(exc))


if __name__ == "__main__":
    # parameter
    file_dir = ""

    if len(sys.argv) > 1:
        file_dir = sys.argv[1]

    file_name = file_dir + "mail_sorter_setting.ini"
    file_name2 = file_dir + "word_setting.ini"
    json_name = file_dir + "client_secret.json"

    if os.path.exists(file_dir + "email_sorter.dat"):
        os.remove(file_dir + 'email_sorter.dat')

    # 설정 데이터 읽기
    ini_file = open(file_name, 'r')
    lines = ini_file.readlines()

    my_token = lines[1].strip('\n')
    channel_id = lines[3].strip('\n')
    channel_list = channel_id.split(" ")
    delay_timer = int(lines[5].strip('\n'))
    msg_format = lines[7].strip('\n')

    ini_file.close()
    
    # 단어 데이터 읽기
    word_file = open(file_name2, 'r')
    lines = word_file.readlines()
    for line in lines:
        if line[0] is '#':
            continue
        temp = line.strip('\n').split(" ")
        if temp[0] is '1':
            word1.append(temp[1])
            temp2 = [temp[2], temp[3]]
            word1_emoji[temp[1]] = temp2
        elif temp[0] is '2':
            word2.append(temp[1])
            temp2 = [temp[2], temp[3]]
            word2_emoji[temp[1]] = temp2
        elif temp[0] is '3':
            word3.append(temp[1])
            temp2 = [temp[2], temp[3]]
            word3_emoji[temp[1]] = temp2

    word_file.close()

    # Logger 초기화
    fileMaxByte = 1024 * 1024 * 100  # 100MB
    logger = logging.getLogger('sorter')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    fileHandler = logging.handlers.RotatingFileHandler(file_dir + 'mail_sorter.log', maxBytes=fileMaxByte, backupCount=10)
    streamHandler = logging.StreamHandler()
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

    # 설정 출력
    logger.info("Telegram Bot Token : " + my_token)
    logger.info("Telegram Channel IDs : " + channel_id)
    logger.info("Delay Timer : " + str(delay_timer) + "sec.")
    logger.info("초기 구성 완료.")

    # 봇 초기화
    my_bot = telegram.Bot(token=my_token)

    # Setup the GMail API
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    store = file.Storage(file_dir + 'credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(json_name, SCOPES)
        creds = tools.run_flow(flow, store)
    service = apiclient.discovery.build('gmail', 'v1', http=creds.authorize(Http()))

    # Call the GMail API
    results = service.users().labels().list(userId='me').execute()

    # 프로그램 시작
    loop(service=service, id='me', bot=my_bot)