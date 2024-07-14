# Solarplant Docker Image

This repository contains the Docker image for my solarplant project.

The system consists of the integrated web server of the solar plant, a Docker container that queries the data, and a MySQL database where the data is stored.

This database can be used, for example, as a datasource for a Grafana dashboard to visualize the collected solar plant data.
## Installation

To install the image directly from GitHub, use the following command on your Docker device:
```bash
curl -sL https://raw.githubusercontent.com/zumbsy/solarplant/main/install.sh | bash
```

## Using Docker Compose

Template `docker-compose.yml`

```yaml
version: '3'
services:
  solarplant:
    image: solarplant:2.1
    container_name: container01
    restart: unless-stopped
    environment:
      WEB_SERVER: 192.168.0.115
      WEB_USERNAME: admin
      WEB_PASSWORD: admin
      MYSQL_USERNAME: root
      MYSQL_PASSWORD: 
      MYSQL_SERVER: 192.168.0.5
      MYSQL_TABLE: solarplant
      MYSQL_DATABASE: solar
      INTERVAL: 600
      LOG: info
```

## Environment Variables

Here are the environment variables that you can customize in the `docker-compose.yml`:

### Required Variables:

- `WEB_SERVER`: The IP address or hostname of the web server.
- `WEB_USERNAME`: The username for the web server.
- `MYSQL_USERNAME`: The username for the MySQL server.
- `MYSQL_SERVER`: The IP address or hostname of the MySQL server.
- `MYSQL_TABLE`: The name of the MySQL table.
- `MYSQL_DATABASE`: The name of the MySQL database.

### Optional Variables:

- `MYSQL_PASSWORD` (default: `""`): The password for the MySQL server.
- `WEB_PASSWORD` (default: `""`): The password for the web server.
- `INTERVAL` (default: `600.0` Seconds): The interval for data retrieval in seconds.
- `LOG` (default: `"info"`): The log level (`"info"`, `"warn"`, `"error"`, `"none"`).



## MySQL Database Schema

To create the table for this project in MySQL, use the following SQL command:

```sql
CREATE TABLE table_name (
    id int(11) AUTO_INCREMENT,
    timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    current_power int(11),
    today_energy int(11),
    total_energy int(11),
    PRIMARY KEY (id)
);
```

## Problems
- If an error occurs, retries are attempted every 20 seconds. During nighttime, the web server of the solar plant is unreachable, resulting in 3 timeout errors per minute.
## ToDo
- Integrate with the sunrisesunset.io API to capture sunrise and sunset times for pausing the script during nighttime.
- Publish the Image to the Docker Repository

## License

This project is licensed under the MIT License. For more information, please refer to the [LICENSE](LICENSE) file.
