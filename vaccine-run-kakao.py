#!/usr/bin/env python3.9 -m nuitka
# -*- coding: utf-8 -*-
import browser_cookie3
import requests
import configparser
import json
import os
import sys
import time
from playsound import playsound
from datetime import datetime
import telepot
import unicodedata
import urllib3
import re
import platform

search_time = 0.2  # Scan the remaining vaccine once every corresponding time. Units: Seconds
urllib3.disable_warnings()
#127.40315938843808
#36.32422482740255
#127.28028356590578
#36.3999757438553
# Get cookies from 'load_cookie()' below.
jar = None


# Loading existing input values
def load_config():
    config_parser = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        try:
            config_parser.read('config.ini')

            while True:
                skip_input = str.lower(input("Do you want to start with the previous setting? Y/N : "))
                if skip_input == "y":
                    skip_input = True
                    break
                elif skip_input == "n":
                    skip_input = False
                    break
                else:
                    print("Please enter Y or N.")

            if skip_input:
                # Loading recent login information if a setup file exists.
                configuration = config_parser['config']
                previous_used_type = configuration["VAC"]
                previous_top_x = configuration["topX"]
                previous_top_y = configuration["topY"]
                previous_bottom_x = configuration["botX"]
                previous_bottom_y = configuration["botY"]
                previous_only_left = configuration["onlyLeft"] == "True"
                return previous_used_type, previous_top_x, previous_top_y, previous_bottom_x, previous_bottom_y, previous_only_left
            else:
                return None, None, None, None, None, None
        except ValueError:
            return None, None, None, None, None, None
    return None, None, None, None, None, None


# Loaded path from [chrome][cookie_file] in cookie.ini.
def load_cookie_config():
    global jar

    config_parser = configparser.ConfigParser(interpolation=None)
    if os.path.exists('cookie.ini'):
        config_parser.read('cookie.ini')
        try:
            cookie_file = config_parser.get(
                'chrome', 'cookie_file', fallback=None)
            if cookie_file is None:
                return None

            indicator = cookie_file[0]
            if indicator == '~':
                cookie_path = os.path.expanduser(cookie_file)
            elif indicator in ('%', '$'):
                cookie_path = os.path.expandvars(cookie_file)
            else:
                cookie_path = cookie_file

            cookie_path = os.path.abspath(cookie_path)

            if os.path.exists(cookie_path):
                return cookie_path
            else:
                print("Cookie file does not exist at the specified path. Try with default values.")
                return None
        except Exception:  # I don't know the exact error, so all of them are Exception.
            return None
    return None


def load_saved_cookie() -> bool:
    #  print('saved cookie loading')
    config_parser = configparser.ConfigParser(interpolation=None)

    global jar

    if os.path.exists('cookie.ini'):
        try:
            config_parser.read('cookie.ini')
            cookie = config_parser['cookie_values']['_kawlt'].strip()

            if cookie is None or cookie == '':
                return False

            jar = {'_kawlt': cookie}
            return True
        except Exception:
            return False

    return False


def dump_cookie(value):
    config_parser = configparser.ConfigParser()
    config_parser.read('cookie.ini')

    with open('cookie.ini', 'w') as cookie_file:
        config_parser['cookie_values'] = {
            '_kawlt': value
        }
        config_parser.write(cookie_file)


# Cookie path is not entered, cookie file is in Default path
# Cookie loaded into global jar function when path is entered or cookie in Default path exists.
def load_cookie_from_chrome() -> None:
    global jar

    cookie_file = load_cookie_config()
    if cookie_file is False:
        return

    if cookie_file is None:
        cookie_path = None
        os_type = platform.system()
        if os_type == "Linux":
            # browser_cookie3 also checks beta version of google chrome's cookie file.
            cookie_path = os.path.expanduser(
                "~/.config/google-chrome/Default/Cookies")
            if os.path.exists(cookie_path) is False:
                cookie_path = os.path.expanduser(
                    "~/.config/google-chrome-beta/Default/Cookies")
        elif os_type == "Darwin":
            cookie_path = os.path.expanduser(
                "~/Library/Application Support/Google/Chrome/Default/Cookies")
        elif os_type == "Windows":
            cookie_path = os.path.expandvars(
                "%LOCALAPPDATA%/Google/Chrome/User Data/Default/Cookies")
        else:  # Jython?
            print("This environment is not supported.")
            close()

        if os.path.exists(cookie_path) is False:
            print("The file does not exist in the default cookie file path. " +
                  "Please refer to the link below and specify the cookie file path.\n" +
                  "https://github.com/SJang1/korea-covid-19-remaining-vaccine-macro/discussions/403")
            close()

    jar = browser_cookie3.chrome(
        cookie_file=cookie_file, domain_name=".kakao.com")

    # Save cookies in cookie.ini.
    for cookie in jar:
        if cookie.name == '_kawlt':
            dump_cookie(cookie.value)
            break


def load_search_time():
    global search_time

    config_parser = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        config_parser.read('config.ini')
        input_time = config_parser.getfloat(
            'config', 'search_time', fallback=0.2)

        if input_time < 0.1:
            search_time = 0.1
        else:
            search_time = input_time


def check_user_info_loaded():
    global jar
    user_info_api = 'https://vaccine.kakao.com/api/v1/user'
    user_info_response = requests.get(
        user_info_api, headers=Headers.headers_vacc, cookies=jar, verify=False)
    user_info_json = json.loads(user_info_response.text)
    if user_info_json.get('error'):
        # The cookies in Cookie.ini may be past their expiration date.
        # Save cookies.ini cookies to 'prev_jar' for comparison.
        prev_jar = jar
        load_cookie_from_chrome()

        # If you find a new cookie in the Chrome browser, start checking again.
        if prev_jar != jar:
            #  print('new cookie value from chrome detected')
            check_user_info_loaded()
            return

        print("Failed to retrieve user information.")
        print("Please check if you are properly logged in to Kakao in the Chrome browser.")
        print("If you can't do it even though you're logged in, " +
              "please go into Kakao Talk and apply for the remaining vaccine notification. " +
              "If you are asked to provide information, please agree and try again.")
        close()
    else:
        user_info = user_info_json.get("user")
        for key in user_info:
            value = user_info[key]
            # print(key, value)
            if key != 'status':
                continue
            if key == 'status' and value == "NORMAL":
                print("Successfully retrieved user information.")
                break
            elif key == 'status' and value == "UNKNOWN":
                print("User whose status is unknown. Please contact 1339 or the health center.")
                close()
            else:
                print("Users who have already been vaccinated or who have been booked.")
                close(success=None)


def fill_str_with_space(input_s, max_size=40, fill_char=" "):
    """
    - Check 2 spaces for long characters and 1 space if short.
    - Maximum length (max_size) is 40, and the actual length of input_s is shorter than this.
    Fill in the remaining characters with fill_char.
    """
    length = 0
    for c in input_s:
        if unicodedata.east_asian_width(c) in ["F", "W"]:
            length += 2
        else:
            length += 1
    return input_s + fill_char * (max_size - length)


# Something is wrong here
def is_in_range(coord_type, coord, user_min_x=-180.0, user_max_y=90.0):
    korea_coordinate = {  # Republic of Korea coordinate
        "min_x": 124.5,
        "max_x": 132.0,
        "min_y": 33.0,
        "max_y": 38.9
    }
    try:
        if coord_type == "x":
            return max(korea_coordinate["min_x"], user_min_x) <= float(coord) <= korea_coordinate["max_x"]
        elif coord_type == "y":
            return korea_coordinate["min_y"] <= float(coord) <= min(korea_coordinate["max_y"], user_max_y)
        else:
            return False
    except ValueError:
        # Prevent entry of values other than float
        return False


# pylint: disable=too-many-branches
def input_config():
    vaccine_candidates = [
        {"name": "Any Vaccine", "code": "ANY"},
        {"name": "pfizer", "code": "VEN00013"},
        {"name": "Moderna", "code": "VEN00014"},
        {"name": "Astrazeneca", "code": "VEN00015"},
        {"name": "Janssen", "code": "VEN00016"},
        {"name": "(Not used)", "code": "VEN00017"},
        {"name": "(Not used)", "code": "VEN00018"},
        {"name": "(Not used)", "code": "VEN00019"},
        {"name": "(Not used)", "code": "VEN00020"},
    ]
    vaccine_type = None
    while True:
        print("=== Vaccine List ===")
        for vaccine in vaccine_candidates:
            if vaccine["name"] == "(Not used)":
                continue
            print(
                f"{fill_str_with_space(vaccine['name'], 10)} : {vaccine['code']}")

        vaccine_type = str.upper(input("Please choose the vaccine code to reserve: ").strip())
        if any(x["code"] == vaccine_type for x in vaccine_candidates) or vaccine_type.startswith("FORCE:"):
            if vaccine_type.startswith("FORCE:"):
                vaccine_type = vaccine_type[6:]

                print("WARNING: You have used forced code entry mode.\n" +
                      "This mode should only be used** if the new vaccine is not registered as a reserved code.\n" +
                      "Please make sure that the code you entered is a vaccine code that works normally.\n" +
                      f"Current Code: f'{vaccine_type}'\n")

                if len(vaccine_type) != 8 or not vaccine_type.startswith("VEN") or not vaccine_type[3:].isdigit():
                    print("The code you entered does not match the current known vaccine code format.")
                    proceed = str.lower(input("Do you want to proceed? Y/N : "))
                    if proceed == "y":
                        pass
                    elif proceed == "n":
                        continue
                    else:
                        print("Please enter Y or N.")
                        continue

            if next((x for x in vaccine_candidates if x["code"] == vaccine_type), {"name": ""})["name"] == "(Not used)":
                print("This is the vaccine code that has not been registered in the current version of the program.\n" +
                      "Please make sure that the code you entered is a vaccine code that works normally.\n" +
                      f"Current Code: '{vaccine_type}'\n")

            break
        else:
            print("Please check the vaccine code.")

    print("After you specify the range of map to search," +
          " look up the vaccine within that range and open the Chrome browser if there are any remaining vaccines.")
    top_x = None
    while top_x is None:
        top_x = input("Please enter the top left x of the square. 127.xxxxxx: ").strip()
        if not is_in_range(coord_type="x", coord=top_x):
            print(f"This is not a valid coordinate value. Input Value: {top_x}")
            top_x = None

    top_y = None
    while top_y is None:
        top_y = input("Please enter the top left y of the square. 37.xxxxxx: ").strip()
        if not is_in_range(coord_type="y", coord=top_y):
            print(f"This is not a valid coordinate value. Input Value: {top_y}")
            top_y = None

    bottom_x = None
    while bottom_x is None:
        bottom_x = input("Please enter the bottom right x of the square 127.xxxxxx: ").strip()
        if not is_in_range(coord_type="x", coord=bottom_x):
            print(f"This is not a valid coordinate value. Input Value: {bottom_x}")
            bottom_x = None

    bottom_y = None
    while bottom_y is None:
        bottom_y = input("Please enter the bottom right y of the square 37.xxxxxx: ").strip()
        if not is_in_range(coord_type="y", coord=bottom_y):
            print(f"This is not a valid coordinate value. Input Value: {bottom_y}")
            bottom_y = None

    only_left = None
    while only_left is None:
        only_left = str.lower(input("Would you like to inquire only hospitals with remaining vaccines? Y/N : "))
        if only_left == "y":
            only_left = True
        elif only_left == "n":
            only_left = False
        else:
            print("Please enter Y or N.")
            only_left = None

    dump_config(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left)
    return vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left


# pylint: disable=too-many-arguments
def dump_config(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left):
    config_parser = configparser.ConfigParser()
    config_parser['config'] = {}
    conf = config_parser['config']
    conf['VAC'] = vaccine_type
    conf["topX"] = top_x
    conf["topY"] = top_y
    conf["botX"] = bottom_x
    conf["botY"] = bottom_y
    conf["search_time"] = str(search_time)
    conf["onlyLeft"] = "True" if only_left else "False"

    with open("config.ini", "w") as config_file:
        config_parser.write(config_file)


def clear():
    if 'win' in sys.platform.lower():
        os.system('cls')
    else:
        os.system('clear')


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def play_tada():
    playsound(resource_path('tada.mp3'))


def play_xylophon():
    playsound(resource_path('xylophon.mp3'))


def close(success=False):
    if success is True:
        play_tada()
        send_msg("Reservation successful for remaining vaccine!! Check your \n KakaoTalk wallet.")
    elif success is False:
        play_xylophon()
        send_msg("The remaining vaccine reservation program has ended with an error.")
    else:
        pass
    input("Press Enter to close...")
    sys.exit()


def pretty_print(json_object):
    for org in json_object["organizations"]:
        if org.get('status') == "CLOSED" or org.get('status') == "EXHAUSTED" or org.get('status') == "UNAVAILABLE":
            continue
        print(
            f"# of Vaccine: {org.get('leftCounts')}\tStatus: {org.get('status')}\tHospital Name: {org.get('orgName')}\tAddress: {org.get('address')}")


class Headers:
    headers_map = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "Origin": "https://vaccine-map.kakao.com",
        "Accept-Language": "en-us",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 KAKAOTALK 9.4.2",
        "Referer": "https://vaccine-map.kakao.com/",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "Keep-Alive",
        "Keep-Alive": "timeout=5, max=1000"
    }
    headers_vacc = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "Origin": "https://vaccine.kakao.com",
        "Accept-Language": "en-us",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 KAKAOTALK 9.4.2",
        "Referer": "https://vaccine.kakao.com/",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "Keep-Alive",
        "Keep-Alive": "timeout=5, max=1000"
    }


def try_reservation(organization_code, vaccine_type):
    reservation_url = 'https://vaccine.kakao.com/api/v2/reservation'
    data = {"from": "Map", "vaccineCode": vaccine_type,
            "orgCode": organization_code, "distance": None}
    response = requests.post(reservation_url, data=json.dumps(
        data), headers=Headers.headers_vacc, cookies=jar, verify=False)
    response_json = json.loads(response.text)
    for key in response_json:
        value = response_json[key]
        if key != 'code':
            continue
        if key == 'code' and value == "NO_VACANCY":
            print("Your application for the remaining vaccine has been closed on a first-come, first-served basis.")
            time.sleep(0.08)
        elif key == 'code' and value == "TIMEOUT":
            print("TIMEOUT, Retry booking.")
            retry_reservation(organization_code, vaccine_type)
        elif key == 'code' and value == "SUCCESS":
            print("Vaccination application successful!!!")
            organization_code_success = response_json.get("organization")
            print(
                f"Hospital Name: {organization_code_success.get('orgName')}\t" +
                f"Phone Number: {organization_code_success.get('phoneNumber')}\t" +
                f"Address: {organization_code_success.get('address')}")
            close(success=True)
        else:
            print("ERROR. Look at the message below and see if your reservation is made or " +
                  "call the hospital for confirmation")
            print(response.text)
            close()


def retry_reservation(organization_code, vaccine_type):
    reservation_url = 'https://vaccine.kakao.com/api/v1/reservation/retry'

    data = {"from": "Map", "vaccineCode": vaccine_type,
            "orgCode": organization_code, "distance": None}
    response = requests.post(reservation_url, data=json.dumps(
        data), headers=Headers.headers_vacc, cookies=jar, verify=False)
    response_json = json.loads(response.text)
    for key in response_json:
        value = response_json[key]
        if key != 'code':
            continue
        if key == 'code' and value == "NO_VACANCY":
            print("Your application for the remaining vaccine has been closed on a first-come, first-served basis.")
            time.sleep(0.08)
        elif key == 'code' and value == "SUCCESS":
            print("Vaccination application successful!!!")
            organization_code_success = response_json.get("organization")
            print(
                f"Hospital Name: {organization_code_success.get('orgName')}\t" +
                f"Phone Number: {organization_code_success.get('phoneNumber')}\t" +
                f"Address: {organization_code_success.get('address')}")
            close(success=True)
        else:
            print("ERROR. Look at the message below and see if your reservation is made or " +
                  "call the hospital for confirmation")
            print(response.text)
            close()


# ===================================== def ===================================== #


# Get Cookie
# driver = selenium.webdriver.Firefox()
# driver.get("https://cs.kakao.com")
# pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))
# cookies = pickle.load(open("cookies.pkl", "rb"))
# for cookie in cookies:
#     driver.add_cookie(cookie)
#     print(cookie)

# pylint: disable=too-many-locals,too-many-statements,too-many-branches,too-many-arguments
def find_vaccine(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left):
    url = 'https://vaccine-map.kakao.com/api/v3/vaccine/left_count_by_coords'
    data = {"bottomRight": {"x": bottom_x, "y": bottom_y}, "onlyLeft": only_left, "order": "latitude",
            "topLeft": {"x": top_x, "y": top_y}}
    done = False
    found = None

    while not done:
        try:
            time.sleep(search_time)
            response = requests.post(url, data=json.dumps(
                data), headers=Headers.headers_map, verify=False, timeout=5)

            try:
                json_data = json.loads(response.text)
                pretty_print(json_data)
                print(datetime.now())

                for x in json_data.get("organizations"):
                    if x.get('status') == "AVAILABLE" or x.get('leftCounts') != 0:
                        found = x
                        done = True
                        break

            except json.decoder.JSONDecodeError as decodeerror:
                print("JSONDecodeError : ", decodeerror)
                print("JSON string : ", response.text)
                close()


        except requests.exceptions.Timeout as timeouterror:
            print("Timeout Error : ", timeouterror)

        except requests.exceptions.SSLError as sslerror:
            print("SSL Error : ", sslerror)
            close()

        except requests.exceptions.ConnectionError as connectionerror:
            print("Connection Error : ", connectionerror)
            # See psf/requests#5430 to know why this is necessary.
            if not re.search('Read timed out', str(connectionerror), re.IGNORECASE):
                close()

        except requests.exceptions.HTTPError as httperror:
            print("Http Error : ", httperror)
            close()

        except requests.exceptions.RequestException as error:
            print("AnyException : ", error)
            close()

    if found is None:
        find_vaccine(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left)
        return None

    print(f"There are {found.get('leftCounts')} Vaccine at {found.get('orgName')}.")
    print(f"Address : {found.get('address')}")
    organization_code = found.get('orgCode')

    # Actual Vaccine Remaining
    vaccine_found_code = None

    if vaccine_type == "ANY":  # ANY Vaccine Selection
        check_organization_url = f'https://vaccine.kakao.com/api/v3/org/org_code/{organization_code}'
        check_organization_response = requests.get(check_organization_url, headers=Headers.headers_vacc, cookies=jar,
                                                   verify=False)
        check_organization_data = json.loads(
            check_organization_response.text).get("lefts")
        for x in check_organization_data:
            if x.get('leftCount') != 0:
                found = x
                print(f"There are {found.get('leftCounts')} Vaccine at {found.get('orgName')}.")
                vaccine_found_code = x.get('vaccineCode')
                break
            else:
                print(f"There is no {x.get('vaccineName')} vaccine.")

    else:
        vaccine_found_code = vaccine_type
        print(f"Try to make a reservation for {vaccine_found_code}.")

    if vaccine_found_code and try_reservation(organization_code, vaccine_found_code):
        return None
    else:
        find_vaccine(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left)
        return None


def main_function():
    got_cookie = load_saved_cookie()
    if got_cookie is False:
        load_cookie_from_chrome()

    load_search_time()
    check_user_info_loaded()
    previous_used_type, previous_top_x, previous_top_y, previous_bottom_x, previous_bottom_y, only_left = load_config()
    if previous_used_type is None:
        vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left = input_config()
    else:
        vaccine_type, top_x, top_y, bottom_x, bottom_y = previous_used_type, previous_top_x, previous_top_y, previous_bottom_x, previous_bottom_y
    find_vaccine(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left)
    close()


def send_msg(msg):
    config_parser = configparser.ConfigParser()
    if os.path.exists('telegram.txt'):
        try:
            config_parser.read('telegram.txt')
            print("Send results to Telegram.")
            tgtoken = config_parser["telegram"]["token"]
            tgid = config_parser["telegram"]["chatid"]
            bot = telepot.Bot(tgtoken)
            bot.sendMessage(tgid, msg)
            return
        except Exception as e:
            print("Telegram Error : ", e)
            return


# ===================================== run ===================================== #
if __name__ == '__main__':
    main_function()
