# Module Imports
import time
from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
import re
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from enum import Enum


class Log(Enum):
    info = 3
    warn = 2
    error = 1


# Init Environment Variables
load_dotenv()

log_level_name = os.getenv('LOG', 'info').lower()
log_level_mapping = {
    'info': Log.info.value,
    'warn': Log.warn.value,
    'error': Log.error.value,
    'none': 0
}

if log_level_name not in log_level_mapping:
    raise KeyError(f"Invalid log level: {log_level_name}")


logLevel: int = log_level_mapping[log_level_name]

def write_log(*text: str, type: Log = Log.info) -> None:
    """
    Prints to Console with different Logging Levels
    See "logLevel"

    :param text: Values seperated by '; '
    :param type: Log: info, warn, error
    :return:
    """
    if type.value <= logLevel:
        print(f"{type.name.upper()} | {'; '.join(text)}")

print(f"Log level set to: {log_level_name.upper()} ({logLevel})")


def check_env_variables(required_vars: list[str], optional_vars_with_defaults: dict[str, str]) -> dict[str, str]:
    """
    Check if all required environment variables are set and set default values for optional ones.
    :param required_vars: List of required environment variables
    :param optional_vars_with_defaults: Dictionary of optional environment variables with their default values
    :return: Dictionary of all environment variables with their values
    :raises EnvironmentError: If any required environment variable is missing
    """
    missing_vars = [var for var in required_vars if os.getenv(var) is None]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

    env_vars = {var: os.getenv(var) for var in required_vars}
    for var, default in optional_vars_with_defaults.items():
        env_vars[var] = os.getenv(var, default)

    return env_vars


# Required Env Variables
required_vars: list[str] = [
    'WEB_USERNAME',
    'WEB_SERVER',
    'MYSQL_USERNAME',
    'MYSQL_SERVER',
    'MYSQL_DATABASE',
    'MYSQL_TABLE'
]

# Optional Env Vars with Default Values
optional_vars_with_defaults: dict[str, str] = {
    'LOG': 'info',
    'INTERVAL': '600',
    'MYSQL_PASSWORD': '',
    'WEB_PASSWORD': ''
}

try:
    env_vars = check_env_variables(required_vars, optional_vars_with_defaults)
    write_log(f"Environment variables: {', '.join(sorted(env_vars.keys()))}")
except EnvironmentError as e:
    write_log(e, type=Log.error)

web_username: str = env_vars['WEB_USERNAME']
web_password: str = env_vars['WEB_PASSWORD']
web_server: str = env_vars['WEB_SERVER']
mysql_username: str = env_vars['MYSQL_USERNAME']
mysql_password: str = env_vars['MYSQL_PASSWORD']
mysql_server: str = env_vars['MYSQL_SERVER']
mysql_database: str = env_vars['MYSQL_DATABASE']
mysql_table: str = env_vars['MYSQL_TABLE']
interval: float = float(env_vars['INTERVAL'])


# HTTP Request Attributes
url: str = f"http://{web_server}/status.html"
headers: dict = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-DE,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-GB;q=0.6,en-US;q=0.5,la;q=0.4",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Referer": f"http://{web_server}/index_cn.html",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
}


def storeData(current_power: int, today_energy: int, total_energy: int) -> None:
    """
    Stores Data into MySQL Database!
    :param current_power: Current Power in Watts
    :param today_energy: Today's Energy in Watt-Hours
    :param total_energy: Total Energy in Watt-Hours
    :return:
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=mysql_server,
            database=mysql_database,
            user=mysql_username,
            password=mysql_password
        )

        if connection.is_connected():
            write_log(f"SQL Connecting to {mysql_server}")
            cursor = connection.cursor()

            # SQL Insert Statement
            insert_query: str = f"""
            INSERT INTO {mysql_table} (current_power, today_energy, total_energy)
            VALUES (%s, %s, %s)
            """
            # Werte, die eingefügt werden sollen
            values: tuple = (current_power, today_energy, total_energy)

            # Sichere Ausführung des Insert-Befehls
            cursor.execute(insert_query, values)
            connection.commit()
            write_log(f"SQL Insert Data to {mysql_database}/{mysql_table}")

    except Error as e:
        write_log(f"Database Connection Error: {e}", type=Log.error)

    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            write_log("SQL Close connection")

def requestWebserver() -> str:
    """
    Connect to Webserver and return Source-Code
    :return:
    """
    try:
        write_log(f"Fetching HTML from {url}")
        response = requests.get(
            url,
            headers=headers,
            auth=HTTPBasicAuth(web_username, web_password),
            verify=False
        )
        if response.status_code == 200:
            write_log(f"HTTP Status: {response.status_code}")

        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        write_log(f"Webserver: {e}", type=Log.error)
        return None


def getValuesFromHtml(sourceCode: str) -> dict[str, int]:
    """
    Get Power and Energy Yields from HTML
    :param sourceCode:
    :return:
    """

    soup: BeautifulSoup = BeautifulSoup(sourceCode, "html.parser")
    # Find all <script> Tags
    for script_tag in soup.find_all('script'):
        script_content = script_tag.string

        if script_content:
            # RegEx Search for the js Variables
            webdata_now_p_match = re.search(r'var webdata_now_p = "([^"]+)"', script_content)
            webdata_today_e_match = re.search(r'var webdata_today_e = "([^"]+)"', script_content)
            webdata_total_e_match = re.search(r'var webdata_total_e = "([^"]+)"', script_content)

            if webdata_now_p_match and webdata_today_e_match and webdata_total_e_match:
                current_power: int = int(webdata_now_p_match.group(1))
                today_energy: int = int(float(webdata_today_e_match.group(1)) * 1000)
                total_energy: int = int(float(webdata_total_e_match.group(1)) * 1000)

                data: dict[str, int] = {
                    'current_power': current_power,
                    'today_energy': today_energy,
                    'total_energy': total_energy
                }
                return data

    return None


def getData() -> dict[str, int]:
    """
    Fetches Data from Webserver. Returns Current Power (W), Today's Energy (Wh) and Total Energy (Wh)
    :return:
    """

    sourceCode: str = requestWebserver()
    if sourceCode is None:
        return None

    data: dict[str, int] = getValuesFromHtml(sourceCode)
    if data is None:
        return None

    return data


def main() -> None:
    """
    Runs the Program
    :return:
    """
    write_log("Initial Run")
    while True:
        write_log(f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
        data = getData()
        write_log(f"Fetched Data: {data}")
        if data and data['total_energy'] > 0:
            storeData(data['current_power'], data['today_energy'], data['total_energy'])
            write_log(f"Sleep: {interval/60} Minutes")
            time.sleep(interval)
            continue
        write_log("Retry in 20 Seconds")
        time.sleep(20)


if __name__ == "__main__":
    main()