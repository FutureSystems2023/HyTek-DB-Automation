import configparser
import logging
import os


config = configparser.ConfigParser()
config.read("config.ini")

log_file_path = os.path.join(os.getcwd(), config["DEFAULT"]["LOG_FILE"])

# Create log file or reinitialize log file if exceed a size
if not os.path.exists(log_file_path):
    with open(log_file_path, 'w') as fp: 
        pass
elif os.path.getsize(log_file_path) > 1048576:  # Create new log file if size > 10MB
    with open(log_file_path, 'w') as fp: 
        pass

logging.basicConfig(
    filename=config["DEFAULT"]["LOG_FILE"], 
    encoding='utf-8', 
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Create uploads folder if not exists
if not os.path.exists(os.path.join(os.getcwd(), config["DEFAULT"]["UPLOAD_DIR"])):
    os.mkdir(config["DEFAULT"]["UPLOAD_DIR"])
