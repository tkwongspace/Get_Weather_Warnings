# Get_Weather_Warnings
 Call Q-Weather (和风天气) API for currently issued weather warnings.

*NOTE: THIS SCRIPT IS STILL UNDER CONSTRUCTION*

> `systemd` service is used for the automation of calling API for current weather warning at startup.
> To stop the service, use `sudo systemctl stop get_weather_warning.service`.
> To check the status of the service, use `sudo systemctl status get_weather_warning.service`.

> uWSGI application is used for remote access to download warning information from MySQL database.
> To set up uWSGI application on the server, 
> cd to the project directory, activate the virtual environment, and use `uwsgi uwsgi_server.ini`.
> To stop the uWSGI application, use `uwsgi stop uwsgi_server.ini`.
> To ultimately kill all uWSGI application, use `sudo pkill -f uwsgi -9`.
