from flask import Flask, jsonify
import logging
import pymysql

from private import my_sql_ip, my_sql_user, my_sql_password


app = Flask(__name__)


# Database connection details
db_host = my_sql_ip()
db_user = my_sql_user()
db_password = my_sql_password()
db_name = 'weather_warnings_db'

logging.basicConfig(level=logging.DEBUG)


def get_db_connection():
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        db=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


@app.route('/weather_warning', methods=['GET'])
def get_latest_warning():
    logging.debug("Entering weather_warning endpoint")
    try:
        # MariaDB connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Get the latest warning
        query = "SELECT * FROM warnings WHERE tag = 'current'"
        cursor.execute(query)
        result = cursor.fetchall()

        # Close the connection
        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        logging.error(f"An error occurred: {e}.")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
