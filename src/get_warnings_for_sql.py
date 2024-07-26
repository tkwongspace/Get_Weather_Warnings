# Save this as get_weather_warning.py
import pymysql
import time
from toolbox import *
from private import my_apikey, my_sql_ip, my_sql_user, my_sql_password


# set up logging
set_up_logging(file=r'./record/weather_log.txt')

# local backup record
local_bkp = r"./record/weather_data.json"

# parameters for api connection
api_key = my_apikey()
base_url = 'https://devapi.qweather.com/v7/warning/now?'
# City code: github.com/qwd/LocationList/blob/master/China-City-List-latest.csv
location_code = '101280108'  # Haizhu 101280108 | Panyu 101280102 | Futian 101280603 | Xiangzhou 101280704
complete_url = base_url + 'location=' + location_code + '&lang=en&key=' + api_key

# define MariaDB (MySQL) connection details
db_config = {
    'user': my_sql_user(),
    'password': my_sql_password(),
    'host': my_sql_ip(),
    'database': 'weather_warnings_db'
}


def main():
    while True:
        # call API to download weather warnings and backup
        # and arrange the downloaded information
        weather_data = get_warning_info(complete_url, local_bkp)        

        # connect to database
        try:
            connection = pymysql.connect(
                user=db_config['user'],
                password=db_config['password'],
                host=db_config['host'],
                database=db_config['database']
            )            
            # store_data_in_database(weather_data, connection)
            cursor = connection.cursor()

            # delete previous warning information
            cursor.execute("DELETE FROM warnings WHERE tag='previous'")

            # update the tag of the 'current' to 'previous'
            cursor.execute("UPDATE warnings SET tag='previous' WHERE tag='current'")

            # insert new data as current
            if not weather_data:
                cursor.execute("""
                    INSERT INTO warnings (id, status, time, typename, color, tag, mark)
                    VALUES (NULL, NULL, NULL, NULL, NULL, 'current', NULL)
                """)
            else:
                for i in range(len(weather_data['id'])):
                    id = weather_data['id'][i]
                    status = weather_data['status'][i]
                    issue_time = weather_data['time'][i]
                    name = weather_data['typeName'][i]
                    color = weather_data['color'][i]
                    mark = weather_data['tag'][i]
                    cursor.execute("""
                        INSERT INTO warnings (id, status, time, typename, color, tag, mark)
                        VALUES (%s, %s, %s, %s, %s, 'current', %s)
                    """, (id, status, issue_time, name, color, mark))
            
            connection.commit()

            print(">> Success in fetching warning info.")
            print("  Update in 90 seconds...")

        except Exception as e:
            print(f">! Error in fetching warning info: {e}.")
            print("   Retry in 90 seconds...")

        finally:
            cursor.close()
            connection.close()

        time.sleep(90)


if __name__ == "__main__":
    main()
