import json

import requests

from kakao.common import close
from kakao.cookie import load_cookie_from_chrome
from kakao.request import headers_vaccine


# 쿠키를 통해 사용자의 정보를 불러오는 함수
def check_user_info_loaded(jar):
    user_info_api = 'https://vaccine.kakao.com/api/v1/user'
    user_info_response = requests.get(user_info_api, headers=headers_vaccine, cookies=jar, verify=False)
    user_info_json = json.loads(user_info_response.text)
    if user_info_json.get('error'):
        # cookie.ini 에 있는 쿠키가 유통기한 지났을 수 있다
        chrome_cookie = load_cookie_from_chrome()

        # 크롬 브라우저에서 새로운 쿠키를 찾았으면 다시 체크 시작 한다
        if jar != chrome_cookie:
            #  print('new cookie value from chrome detected')
            check_user_info_loaded(chrome_cookie)
            return

        print("Failed to retrieve user information.")
        print("Please check if you are properly logged in to Kakao in Chrome browser.")
        print("If you can't do it even though you're logged in, please go into Kakao Talk and apply for the remaining vaccine notification. If you agree to provide information, please agree and try again.")
        close()
    else:
        user_info = user_info_json.get("user")
        if user_info['status'] == "NORMAL":
            print(f"Hello {user_info['name']}.")
        elif user_info['status'] == "UNKNOWN":
            print("User whose status is unknown. Please contact 1339 or the health center.")
            close(success=None)
        elif user_info['status'] == "REFUSED":
            print(f"{user_info['name']} is identified as a user who booked a vaccine and did not visit. Reservations for remaining vaccines are not available.")
            close(success=None)
        elif user_info['status'] == "ALREADY_RESERVED" or user_info['status'] == "ALREADY_VACCINATED":
            print(f"{user_info['name']} is a user who has already been booked or inoculated.")
            close(success=None)
        else:
            print(f"Unknown status code. Status code:{user_info['status']}")
            print("Please create Isues with status code information.")
            close()
