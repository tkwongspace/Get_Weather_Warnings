import json
import logging
import requests
import time

from datetime import datetime


# def connect_to_mysql(sql_user, sql_pw, sql_host, sql_db):
#     return pymysql.connect(
#         user=sql_user,
#         password=sql_pw,
#         host=sql_host,
#         database=sql_db
#     )


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
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
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


def set_up_logging(file):
    return logging.basicConfig(
        level=logging.INFO,
        filename=file,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
