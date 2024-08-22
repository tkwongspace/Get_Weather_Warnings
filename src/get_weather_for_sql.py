# Download and write weather information to SQL database.
# Great appreciation to Seniverse API.
from toolbox import *
from private import my_seni_key, my_sql_ip, my_sql_user, my_sql_password


# set up logging
set_up_logging(file=r'./record/weather_log.txt')

# parameters for api connection
api_key = my_seni_key()
location = 'guangzhou'
url_cur_weather = ('https://api.seniverse.com/v3/weather/now.json?key='
                   + api_key
                   + '&location='
                   + location
                   + '&language=zh-Hans&unit=c')
url_forecast = ('https://api.seniverse.com/v3/weather/daily.json?key='
                + api_key
                + '&location='
                + location
                + '&language=zh-Hans&unit=c&start=0&days=3')

# define MariaDB (MySQL) connection details
db_config = {
    'user': my_sql_user(),
    'password': my_sql_password(),
    'host': my_sql_ip(),
    'database': 'weather_db'
}


def main():
    while True:
        # call API to download weather information
        cur_weather = get_weather(url_cur_weather)
        forecast_weather = get_forecast(url_forecast)

        # connect to database
        try:
            connection = connect_to_mysql(db_config)

            with connection.cursor() as cursor:
                # insert weather data
                code = cur_weather['code']
                cn_text = cur_weather['cn']
                en_text = cur_weather['en']
                temp = cur_weather['temp']
                weather_query = """
                    INSERT INTO weather (weather_code, cn, en, temp)
                    VALUES (%s, %s, %s)
                """
                weather_data = (code, cn_text, en_text, temp)
                cursor.execute(weather_query, weather_data)

                # insert forecast data
                for date, values in forecast_weather.items():
                    forecast_query = """
                        INSERT INTO forecast (date, day_code, day_cn, day_en, night_code, night_cn, night_en, max_temp, min_temp, prcp, wdir, wspd, wscl, hum)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(forecast_query, (date, *values))

            # commit the transaction
            connection.commit()

        except Exception as e:
            logging.error(f">!{time.localtime(time.time())} Error in fetching weather info: {e}.")

        finally:
            connection.close()

        time.sleep(900)    # API updates every 15 minutes


if __name__ == "__main__":
    main()
