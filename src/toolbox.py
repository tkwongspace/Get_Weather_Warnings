import json
import logging
import pymysql
import requests
import time

from datetime import datetime


def ask_api(url):
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data


def connect_to_mysql(config_dict):
    return pymysql.connect(
        user=config_dict['user'],
        password=config_dict['password'],
        host=config_dict['host'],
        database=config_dict['database']
    )


def find_duplicate_warnings(name_list, color_list):
    """
    Finds duplicate warnings (with the same type name & color) and returns their indices in issued warnings.

    :param name_list: The list of warning names, which correspond to {typename} from qWeather API.
    :param color_list: The list of warning colors, which correspond to {level} from qWeather API.
    :return:
        A list of tuples, where each tuple contains the indices of a duplicate combination.
    """
    duplicates = []
    seen = {}
    for i, a in enumerate(name_list):
        for j, b in enumerate(color_list):
            combined_attribute = f"{a}_{b}"
            if combined_attribute in seen:
                duplicates.append(((i, j), seen[combined_attribute]))
            else:
                seen[combined_attribute] = (i, j)


def get_forecast(url):
    data = ask_api(url)
    daily = data['daily']
    # arrange information
    forecast = {}
    for f in daily:
        date = f['date']
        forecast[date] = [f['code_day'],                       # weather code at day
                          f['text_day'],                       # weather at day [CN]
                          seni_weather_codes[f['code_day']],   # weather at day [EN]
                          f['code_night'],                     # weather code at night
                          f['text_night'],                     # weather at night [CN]
                          seni_weather_codes[f['code_night']], # weather at night [EN]
                          f['high'],                           # max temperature
                          f['low'],                            # min temperature
                          f['rainfall'],                       # precipitation in mm
                          f['wind_direction'],                 # wind direction text
                          f['wind_speed'],                     # wind speed in kmph
                          f['wind_scale'],                     # wind level
                          f['humidity']]                       # humidity in %
    return forecast


def get_previous_record(file):
    try:
        with open(file, "r") as f:
            previous_response = json.load(f)
            if previous_response['warning']:
                previous_id = [w['id'] for w in previous_response['warning']]
                # previous_name = [w['typeName'] for w in previous_response['warning']]
                # previous_status = [w['status'] for w in previous_response['warning']]
                # previous_color = [w['severityColor'] for w in previous_response['warning']]
                # previous_level = [w['level'] for w in previous_response['warning']]
                # previous_time = [w['startTime'] for w in previous_response['warning']]
            else:
                previous_id = []
            return previous_id

    except FileNotFoundError:
        logging.error(f">!{time.localtime(time.time())} Previous record not found.")


def get_warning_info(url, backup_record):
    # get previous ID stored in local file
    previous_id = get_previous_record(backup_record)   

    # call the API
    try:
        data = ask_api(url)
        if data['code'] == "204":
            logging.error(f">!{time.localtime(time.time())} Remote data unavailable.")

        warnings = data['warning']
        
        # backup warning info at local file
        with open(backup_record, "w") as f:
            json.dump(data, f)

        if warnings:
            # create dictionary for weather info
            current_warnings = read_warnings(warnings, previous_id)
        else:
            current_warnings = {}
        
        return current_warnings
    
    except requests.exceptions.RequestException as e:
        logging.error(f">!{time.localtime(time.time())} Error in fetching warning data: {e}.")


def get_weather(url):
    data = ask_api(url)
    weather = data['now']

    # arrange information
    weather_keys = ['code', 'cn', 'en', 'temp']
    current = {key: [] for key in weather_keys}

    current['cn'] = weather['text']
    current['code'] = weather['code']
    current['en'] = seni_weather_codes[weather['code']]
    current['temp'] = weather['temperature']

    return current


# define the priority levels
priority_levels = {
    "White": 1,
    "Blue": 2,
    "Green": 3,
    "Yellow": 4,
    "Orange": 5,
    "Red": 6,
    "Black": 7
}


def read_warnings(warnings, previous_warning_ids):
    # get the number of warnings
    warning_numbers = len(warnings)
    # get warning information
    warnings_id = [w['id'] for w in warnings]
    warnings_name = [w['typeName'] for w in warnings]
    warnings_status = [w['status'] for w in warnings]
    warnings_color = [w['severityColor'] for w in warnings]
    warnings_level = [w['level'] for w in warnings]  # FutureWarning: Will be aborted in short time.
    warnings_time = [w['startTime'] for w in warnings]
    warnings_time_formatted = [datetime.strptime(t, '%Y-%m-%dT%H:%M%z').strftime('%Y-%m-%d %H:%M') for t in warnings_time]

    # filter warnings with priority check
    warning_information = ['tag', 'id', 'typeName', 'status', 'color', 'time']
    current = {key: [] for key in warning_information}
    for i in range(0, warning_numbers):
        # check if duplicate ID
        if warnings_id[i] in previous_warning_ids:
            current['tag'].append('Maintained')
        else:
            current['tag'].append('New-Issued')
        # check if duplicate warning type
        warning_type = warnings_name[i]
        # the value of warning level and warning severity color are still unstable
        warning_color = warnings_level[i] if warnings_color[i] == "" else warnings_color[i]
        if warning_type in current['typeName']:
            duplicate_index = current['typeName'].index(warning_type)
            # if the warning has been recorded, compare priorities
            if priority_levels[warnings_color[i]] > priority_levels[current['color'][duplicate_index]]:
                # replace thw lower priority item
                current['id'][duplicate_index] = warnings_id[i]
                current['status'][duplicate_index] = warnings_status[i]
                current['time'][duplicate_index] = warnings_time_formatted[i]
                current['typeName'][duplicate_index] = warnings_name[i]
                current['color'][duplicate_index] = warning_color
        else:
            # add the item if it's not seen yet
            current['id'].append(warnings_id[i])
            current['status'].append(warnings_status[i])
            current['time'].append(warnings_time_formatted[i])
            current['typeName'].append(warnings_name[i])
            current['color'].append(warning_color)

    return current


seni_weather_codes = {
    0: "Sunny",     # for day
    1: "Clear",     # for night
    4: "Cloudy",
    5: "Partly Cloudy",     # for day
    6: "Partly Cloudy",     # for night
    7: "Mostly Cloudy",     # for day
    8: "Mostly Cloudy",     # for night
    9: "Overcast",
    10: "Shower",
    11: "Thundershower",
    12: "Thundershower with Hail",
    13: "Light Rain",
    14: "Moderate Rain",
    15: "Heavy Rain",
    16: "Storm",
    17: "Heavy Storm",
    18: "Severe Storm",
    19: "Ice Rain",
    20: "Sleet",
    21: "Snow Flurry",
    22: "Light Snow",
    23: "Moderate Snow",
    24: "Heavy Snow",
    25: "Snowstorm",
    26: "Dust",
    27: "Sand",
    28: "Duststorm",
    29: "Sandstorm",
    30: "Foggy",
    31: "Haze",
    32: "Windy",
    33: "Blustery",
    34: "Hurricane",
    35: "Tropical Storm",
    36: "Tornado",
    37: "Cold",
    38: "Hot",
    99: "unknown"
}


def set_up_logging(file):
    return logging.basicConfig(
        level=logging.INFO,
        filename=file,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
