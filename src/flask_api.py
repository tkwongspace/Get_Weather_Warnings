from flask import Flask, jsonify
import pymysql

from private import my_sql_ip, my_sql_user, my_sql_password


app = Flask(__name__)


@app.route('/weather_warning', methods=['GET'])
def get_latest_warning():
    # MariaDB connection
    db = pymysql.connect(
        host=my_sql_ip,
        user=my_sql_user,
        password=my_sql_password,
        database="weather_warnings_db"
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Get the latest warning
    cursor.execute("SELECT * FROM warnings ORDER BY timestamp DESC LIMIT 1")
    result = cursor.fetchone()

    # Close the connection
    cursor.close()
    db.close()

    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
