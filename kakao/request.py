import json
import re
import time
from datetime import datetime

import requests
import urllib3

from kakao.common import pretty_print, close

urllib3.disable_warnings()
header_map = {
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

headers_vaccine = {
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


# pylint: disable=too-many-locals,too-many-statements,too-many-branches,too-many-arguments
def find_vaccine(cookie, search_time, vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left, exclusions):
    url = 'https://vaccine-map.kakao.com/api/v3/vaccine/left_count_by_coords'
    data = {"bottomRight": {"x": bottom_x, "y": bottom_y}, "onlyLeft": only_left, "order": "count",
            "topLeft": {"x": top_x, "y": top_y}}
    done = False
    found = None

    while not done:
        try:
            time.sleep(search_time)
            response = requests.post(url, data=json.dumps(data), headers=header_map, verify=False, timeout=5)

            try:
                json_data = json.loads(response.text)

                for x in json_data.get("organizations"):
                    if x.get('status') == "AVAILABLE" or x.get('leftCounts') != 0:
                        found = x
                        done = True
                        break

                if not done:
                    pretty_print(json_data)
                    print(datetime.now())

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
        find_vaccine(cookie, search_time, vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left, exclusions)
        return None

    print(f"{found.get('leftCounts')} vaccines have been found at {found.get('orgName')}!")
    print(f"Address : {found.get('address')}")
    organization_code = found.get('orgCode')

    # 실제 백신 남은수량 확인
    vaccine_found_code = None

    if vaccine_type == "ANY":  # ANY vaccine selection with exclusion check
        check_organization_url = f'https://vaccine.kakao.com/api/v3/org/org_code/{organization_code}'
        check_organization_response = requests.get(check_organization_url, headers=headers_vaccine, cookies=cookie, verify=False)
        check_organization_data = json.loads(check_organization_response.text).get("lefts")
        for x in check_organization_data:
            if x.get('leftCount') != 0:
                print(f"Vaccine {x.get('vaccineName')} has been found with {x.get('leftCount')} remaining doses.")
                found_code = x.get('vaccineCode')
                if found_code in exclusions:
                    print(f"Vaccine {found_code} is available, but was excluded.")
                else:
                    vaccine_found_code = found_code
                    break
            else:
                print(f"Vaccine {x.get('vaccineName')} is unavailable.")

    else:
        vaccine_found_code = vaccine_type
        print(f"Attempt to make a reservation for {vaccine_found_code}.")

    if vaccine_found_code and try_reservation(organization_code, vaccine_found_code, cookie):
        return None
    else:
        find_vaccine(cookie, search_time, vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left, exclusions)
        return None


def try_reservation(organization_code, vaccine_type, jar):
    reservation_url = 'https://vaccine.kakao.com/api/v2/reservation'
    data = {"from": "List", "vaccineCode": vaccine_type,
            "orgCode": organization_code, "distance": None}
    response = requests.post(reservation_url, data=json.dumps(data), headers=headers_vaccine, cookies=jar, verify=False)
    response_json = json.loads(response.text)
    for key in response_json:
        value = response_json[key]
        if key != 'code':
            continue
        if key == 'code' and value == "NO_VACANCY":
            print("Your application for the remaining vaccine has been closed on a first-come, first-served basis.")
        elif key == 'code' and value == "TIMEOUT":
            print("TIMEOUT, Retry booking.")
            retry_reservation(organization_code, vaccine_type, jar)
        elif key == 'code' and value == "SUCCESS":
            print("Vaccination application successful!!!")
            organization_code_success = response_json.get("organization")
            print(
                f"Hospital Name: {organization_code_success.get('orgName')}\t" +
                f"Phone Number: {organization_code_success.get('phoneNumber')}\t" +
                f"Address: {organization_code_success.get('address')}")
            close(success=True)
        else:
            print("ERROR. Look at the message below and see if you have a reservation at the hospital or 1339 that you applied for.")
            print(response.text)
            close()


def retry_reservation(organization_code, vaccine_type, jar):
    reservation_url = 'https://vaccine.kakao.com/api/v2/reservation/retry'

    data = {"from": "List", "vaccineCode": vaccine_type,
            "orgCode": organization_code, "distance": None}
    response = requests.post(reservation_url, data=json.dumps(data), headers=headers_vaccine, cookies=jar, verify=False)
    response_json = json.loads(response.text)
    for key in response_json:
        value = response_json[key]
        if key != 'code':
            continue
        if key == 'code' and value == "NO_VACANCY":
            print("Your application for the remaining vaccine has been closed on a first-come, first-served basis.")
        elif key == 'code' and value == "SUCCESS":
            print("Vaccination application successful!!!")
            organization_code_success = response_json.get("organization")
            print(
                f"Hospital Name: {organization_code_success.get('orgName')}\t" +
                f"Phone Number: {organization_code_success.get('phoneNumber')}\t" +
                f"Address: {organization_code_success.get('address')}")
            close(success=True)
        else:
            print("ERROR. Look at the message below and see if you have a reservation at the hospital or 1339 that you applied for.")
            print(response.text)
            close()
