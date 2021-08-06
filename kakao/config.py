import configparser
import os

from kakao.common import fill_str_with_space


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
        # float 이외 값 입력 방지
        return False

# Disable pylint warnings
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def input_config():
    vaccine_candidates = [
        {"name": "Any Vaccine", "code": "ANY"},
        {"name": "Pfizer", "code": "VEN00013"},
        {"name": "Moderna", "code": "VEN00014"},
        {"name": "Astrazeneca", "code": "VEN00015"},
        {"name": "Johnson", "code": "VEN00016"},
        {"name": "(미사용)", "code": "VEN00017"},
        {"name": "(미사용)", "code": "VEN00018"},
        {"name": "(미사용)", "code": "VEN00019"},
        {"name": "(미사용)", "code": "VEN00020"},
    ]
    vaccine_type = None
    exclusions = []
    while True:
        # Select the vaccine
        print("=== Vaccine List ===")
        for vaccine in vaccine_candidates:
            if vaccine["name"] == "(미사용)":
                continue
            print(
                f"{fill_str_with_space(vaccine['name'], 10)} : {vaccine['code']}")
        print("[Note: you can select ANY and exclude some vaccines later]")
        vaccine_type = str.upper(input("Please enter the vaccine code: ").strip())
        
        # Select exclusions from "ANY" method
        if vaccine_type == "ANY":
            while True:
                print("=== Selected Vaccines List ===")
                for vaccine in vaccine_candidates:
                    if vaccine["name"] == "(미사용)" or vaccine["code"] == "ANY" or vaccine["code"] in exclusions:
                        continue
                    print(f"{fill_str_with_space(vaccine['name'], 10)} : {vaccine['code']}")
                exclusion = str.upper(input("Please enter the code of the vaccine you want to exclude or enter N to exit: ").strip())
                if exclusion == "N":
                    break
                if any(x["code"] == exclusion for x in vaccine_candidates):
                    if exclusion == "ANY":
                        print("ANY is not a valid input")
                    elif exclusion not in exclusions:
                        exclusions.append(exclusion)
                    else:
                        print("Vaccine was already added to exclusions!")
                else:
                    print("Unknown vaccine code inserted, please check!")
                
        if any(x["code"] == vaccine_type for x in vaccine_candidates) or vaccine_type.startswith("FORCE:"):
            if vaccine_type.startswith("FORCE:"):
                vaccine_type = vaccine_type[6:]

                print("WARNING: You have used forced code entry mode.\n" +
                      "This mode should only be used** if the new vaccine is not registered as a reserved code.\n" +
                      "Please make sure that the code you entered is a vaccine code that works normally." +
                      f"Vaccine Code: '{vaccine_type}'\n")

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

            if next((x for x in vaccine_candidates if x["code"] == vaccine_type), {"name": ""})["name"] == "(미사용)":
                print("This is the vaccine code that has not been registered in the current version of the program for future use.\n" +
                      "Please make sure that the code you entered is a vaccine code that works normally.\n" +
                      f"Vaccine Code: '{vaccine_type}'\n")

            break
        else:
            print("Unknown vaccine code inserted, please check!")

    print("After you specify a range of vaccines in a square shape," +
          " check the vaccine within that range and try to make an appointment with the hospital if there are any remaining vaccines.")
    print("You can right-click the desired location on the Google Map to copy the map.")
    top_x = None
    top_y = None
    while top_x is None or top_y is None:
        top_y, top_x = input("Please enter the top left coordinates (Daejeon: 36.32346792518988, 127.46080403718007):").strip().split(",")
        if not is_in_range(coord_type="x", coord=top_x) or not is_in_range(coord_type="y", coord=top_y):
            print(f"This is not a valid coordinate value. Input Value : {top_y}, {top_x}")
            top_x = None
            top_y = None
        else:
            top_x = top_x.strip()
            top_y = top_y.strip()

    bottom_x = None
    bottom_y = None
    while bottom_x is None or bottom_y is None:
        bottom_y, bottom_x = input("Please enter the bottom right coordinates (Daejeon: 36.431638008998874, 127.2857236995207): ").strip().split(",")
        if not is_in_range(coord_type="x", coord=bottom_x) or not is_in_range(coord_type="y", coord=bottom_y):
            print(f"This is not a valid coordinate value. Input Value : {bottom_y}, {bottom_x}")
            bottom_x = None
            bottom_y = None
        else:
            bottom_x = bottom_x.strip()
            bottom_y = bottom_y.strip()

    only_left = None
    while only_left is None:
        only_left = str.lower(input("Do you want to check only hospitals with remaining vaccines? Y/N : "))
        if only_left == "y":
            only_left = True
        elif only_left == "n":
            only_left = False
        else:
            print("Please enter Y or N.")
            only_left = None

    dump_config(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left, exclusions)
    return vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left, exclusions


# 기존 입력 값 로딩
def load_config():
    config_parser = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        try:
            config_parser.read('config.ini')
            while True:
                skip_input = str.lower(input("Do you want to search with the previous information? Y/N : "))
                if skip_input == "y":
                    skip_input = True
                    break
                elif skip_input == "n":
                    skip_input = False
                    break
                else:
                    print("Please enter Y or N.")

            if skip_input:
                try:
                    # 설정 파일이 있으면 최근 로그인 정보 로딩
                    configuration = config_parser['config']
                    previous_used_type = configuration["VAC"]
                    previous_top_x = configuration["topX"]
                    previous_top_y = configuration["topY"]
                    previous_bottom_x = configuration["botX"]
                    previous_bottom_y = configuration["botY"]
                    previous_only_left = configuration["onlyLeft"] == "True"
                    previous_exclusions = configuration["exclusions"].split(',')
                    return previous_used_type, previous_top_x, previous_top_y, previous_bottom_x, previous_bottom_y, previous_only_left, previous_exclusions
                except KeyError:
                    print('No information was previously entered.')
            else:
                return None, None, None, None, None, None, None
        except ValueError:
            return None, None, None, None, None, None, None
    return None, None, None, None, None, None, None


# pylint: disable=too-many-arguments
def dump_config(vaccine_type, top_x, top_y, bottom_x, bottom_y, only_left, exclusions, search_time=0.1):
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
    conf["exclusions"] = ",".join(exclusions) # list into comma separated variables
    
    with open("config.ini", "w") as config_file:
        config_parser.write(config_file)


def load_search_time():
    config_parser = configparser.ConfigParser()
    search_time = 0.1
    if os.path.exists('config.ini'):
        config_parser.read('config.ini')
        input_time = config_parser.getfloat('config', 'search_time', fallback=0.1)

        if input_time < 0.05:
            confirm_input = None
            while confirm_input is None:
                confirm_input = str.lower(input("There is a risk of account suspension if the delay is excessively reduced." +
                                                " Would you like to go on? Y/N : "))
                if confirm_input == "y":
                    search_time = input_time
                elif confirm_input == "n":
                    print("The search cycle is set to the default of 0.1.")
                else:
                    print("Please enter Y or N.")
                    confirm_input = None
        else:
            search_time = input_time
    return search_time
