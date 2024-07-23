# Save this as get_weather_warning.py
import pymysql
import requests

from toolbox import *
from private import my_apikey, my_sql_ip, my_sql_user, my_sql_password


# set up logging
set_up_logging(file=r'../record/weather_log.txt')

# parameters for api connection
api_key = my_apikey()
base_url = 'https://devapi.qweather.com/v7/warning/now?'
location_code = '101310215'  # City code: github.com/qwd/LocationList/blob/master/China-City-List-latest.csv
complete_url = base_url + 'location=' + location_code + '&lang=en&key=' + api_key

# MariaDB connection
db = pymysql.connect(
    host=my_sql_ip(),
    user=my_sql_user(),
    password=my_sql_password(),
    database="weather_warnings_db"
)
cursor = db.cursor()

# restore previous record
pre_id = get_previous_record("../record/weather_data.json")

# Fetch weather warning data
try:
    response = requests.get(complete_url)
    response.raise_for_status()  # raise an exception for bad status codes

    data = response.json()
    warnings = data['warning']
    if warnings:
        current_warnings = read_warnings(warnings)
        # arrange warning information for database
        warnings_id = current_warnings['id']
        warnings_status = current_warnings['status']
        warnings_type = current_warnings['typeName']
        warnings_color = current_warnings['color']
        warnings_issue_time = current_warnings['time']
        # save the warning information
        with open("../record/weather_data.json", "w") as outfile:
            json.dump(data, outfile)
    else:
        warnings_id = None
        warnings_status = None
        warnings_type = None
        warnings_color = None
        warnings_issue_time = None
except requests.exceptions.RequestException as e:
    logging.error(f">! Error fetching warning data: {e}.")

# Process and insert data into database
query = "INSERT INTO warnings (id, status, time, typename, color) VALUES (%s, %s, %s, %s, %s)"

for i in range(len(warnings_id)):
    values = (warnings_id[i], warnings_status[i], warnings_issue_time[i], warnings_type[i], warnings_color[i])
    cursor.execute(query, values)

db.commit()

# Close the connection
cursor.close()
db.close()
