import requests
from datetime import datetime

from private import my_apikey
from toolbox import *


# set up logging
set_up_logging(file=r'../record/weather_log.txt')

# set up api
api_key = my_apikey()
base_url = 'https://devapi.qweather.com/v7/warning/now?'
location_code = '101310215'  # https://github.com/qwd/LocationList/blob/master/China-City-List-latest.csv

complete_url = base_url + 'location=' + location_code + '&lang=en&key=' + api_key

# restore previous record
pre_id = get_previous_record("../record/weather_data.json")

# call the api
try:
    response = requests.get(complete_url)
    response.raise_for_status()  # raise an exception for bad status codes

    data = response.json()
    warnings = data['warning']
    if warnings:
        current_warning = read_warnings(warnings)

        # report current warnings
        for ci in range(0, len(current_warning['id'])):
            name = current_warning['typeName'][ci]
            status = current_warning['status'][ci]
            color = current_warning['color'][ci]
            issue_time = current_warning['time'][ci]
            issue_time = datetime.strptime(issue_time, '%Y-%m-%dT%H:%M%z')
            if current_warning['tag'][ci] == 'New-Issued':
                print(f">! [NEW WARNING] {name} warning [{color}] {status} "
                      f"since {issue_time.strftime('%Y-%m-%d %H:%M')}.")
            elif current_warning['tag'][ci] == 'Remain':
                print(f">> [PERSISTING] {name} warning [{color}] since {issue_time.strftime('%Y-%m-%d %H:%M')}.")

        # save the data
        with open("../record/weather_data.json", "w") as f:
            json.dump(data, f)

    else:
        print(">> No warnings active now.")

except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching weather data: {e}")
