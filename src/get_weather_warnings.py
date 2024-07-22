import requests
import logging
import json
from datetime import datetime
from apikey.apikey import my_apikey


# def find_duplicate_warnings(name_list, color_list):
#     """
#     Finds duplicate warnings (with the same type name & color) and returns their indices in issued warnings.
#
#     :param name_list: The list of warning names, which correspond to {typename} from qWeather API.
#     :param color_list: The list of warning colors, which correspond to {level} from qWeather API.
#     :return:
#         A list of tuples, where each tuple contains the indices of a duplicate combination.
#     """
#     duplicates = []
#     seen = {}
#     for i, a in enumerate(name_list):
#         for j, b in enumerate(color_list):
#             combined_attribute = f"{a}_{b}"
#             if combined_attribute in seen:
#                 duplicates.append(((i, j), seen[combined_attribute]))
#             else:
#                 seen[combined_attribute] = (i, j)


# set up logging
logging.basicConfig(
    level=logging.INFO,
    filename='../record/weather_log.txt',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# set up api
api_key = my_apikey()
base_url = 'https://devapi.qweather.com/v7/warning/now?'
location_code = '101280108'  # https://github.com/qwd/LocationList/blob/master/China-City-List-latest.csv

complete_url = base_url + 'location=' + location_code + '&lang=en&key=' + api_key

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

# restore previous record


# call the api
try:
    response = requests.get(complete_url)
    response.raise_for_status()  # raise an exception for bad status codes

    data = response.json()
    warnings = data['warning']
    if warnings:
        # get the number of warnings
        warning_numbers = len(warnings)
        # get warning information
        warnings_id = [w['id'] for w in warnings]
        warnings_name = [w['typeName'] for w in warnings]
        warnings_status = [w['status'] for w in warnings]
        warnings_color = [w['severityColor'] for w in warnings]
        warnings_level = [w['level'] for w in warnings]  # FutureWarning: Will be aborted in short time.
        warnings_time = [w['startTime'] for w in warnings]

        # filter warnings with priority check
        warning_information = ['id', 'typeName', 'status', 'color', 'time']
        current_warning = {key: [] for key in warning_information}
        for i in range(0, warning_numbers):
            # check if duplicate ID

            # check if duplicate warning type
            warning_type = warnings_name[i]
            # the value of warning level and warning severity color are still unstable
            warning_color = warnings_level[i] if warnings_color[i] == "" else warnings_color[i]
            if warning_type in current_warning['typeName']:
                duplicate_index = current_warning['typeName'].index(warning_type)
                # if the warning has been recorded, compare priorities
                if priority_levels[warnings_color[i]] > priority_levels[current_warning['color'][duplicate_index]]:
                    # replace thw lower priority item
                    current_warning['id'][duplicate_index] = warnings_id[i]
                    current_warning['status'][duplicate_index] = warnings_status[i]
                    current_warning['time'][duplicate_index] = warnings_time[i]
                    current_warning['typeName'][duplicate_index] = warnings_name[i]
                    current_warning['color'][duplicate_index] = warning_color
            else:
                # add the item if it's not seen yet
                current_warning['id'].append(warnings_id[i])
                current_warning['status'].append(warnings_status[i])
                current_warning['time'].append(warnings_time[i])
                current_warning['typeName'].append(warnings_name[i])
                current_warning['color'].append(warning_color)

        # report current warnings
        for ci in range(0, len(current_warning['id'])):
            name = current_warning['typeName'][ci]
            status = current_warning['status'][ci]
            color = current_warning['color'][ci]
            issue_time = current_warning['time'][ci]
            issue_time = datetime.strptime(issue_time, '%Y-%m-%dT%H:%M%z')
            print(f">> The {color} item for {name} is {status} since {issue_time.strftime('%Y-%m-%d %H:%M')}.")

            with open("../record/weather_data.json", "w") as f:
                json.dump(data, f)
    else:
        print(">> No warnings active now.")

except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching weather data: {e}")
