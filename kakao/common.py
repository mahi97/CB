import os
import sys
import configparser
import unicodedata

import telepot
from playsound import playsound, PlaysoundException


def close(success=False):
    if success is True:
        play_tada()
        send_msg("Reservation was successful!! Check your \n KakaoTalk wallet.")
    elif success is False:
        play_xylophon()
        send_msg("The remaining vaccine reservation program has ended with an error.")
    else:
        pass
    input("Press Enter to close...")
    sys.exit()


def clear():
    if 'win' in sys.platform.lower():
        os.system('cls')
    else:
        os.system('clear')


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def play_tada():
    try:
        playsound(resource_path('tada.mp3'))
    except PlaysoundException:
        pass


def play_xylophon():
    try:
        playsound(resource_path('xylophon.mp3'))
    except PlaysoundException:
        pass


def send_msg(msg):
    config_parser = configparser.ConfigParser()
    if os.path.exists('telegram.txt'):
        try:
            config_parser.read('telegram.txt')
            print("Send results to Telegram.")
            telegram_token = config_parser["telegram"]["token"]
            telegram_id = config_parser["telegram"]["chatid"]
            bot = telepot.Bot(telegram_token)
            bot.sendMessage(telegram_id, msg)
            return
        except Exception as e:
            print("Telegram Error : ", e)
            return


def pretty_print(json_object):
    for org in json_object["organizations"]:
        if org.get('status') == "CLOSED" or org.get('status') == "EXHAUSTED" or org.get('status') == "UNAVAILABLE":
            continue
        print(f"Number of Vaccine: {org.get('leftCounts')}\tStatus: {org.get('status')}\tHospital Name: {org.get('orgName')}\tAddress: {org.get('address')}")


def fill_str_with_space(input_s, max_size=40, fill_char=" "):
    """
    - ????????? ??? ????????? 2????????? ????????????, ????????? 1????????? ?????????.
    - ?????? ??????(max_size)??? 40??????, input_s??? ?????? ????????? ????????? ?????????
    ?????? ????????? fill_char??? ?????????.
    """
    length = 0
    for c in input_s:
        if unicodedata.east_asian_width(c) in ["F", "W"]:
            length += 2
        else:
            length += 1
    return input_s + fill_char * (max_size - length)
