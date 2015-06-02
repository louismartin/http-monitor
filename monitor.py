# Run the HTTP monitor with parameters from parameters.cfg

from log_handler import LogHandler
import configparser


config = configparser.ConfigParser()
config.read("parameters.cfg")

logPath = str(config.get("Monitor", "logPath"))
refreshPeriod = float(config.get("Monitor", "refreshPeriod"))
treshold = float(config.get("Monitor", "treshold"))
monitorDuration = float(config.get("Monitor", "monitorDuration"))
logHandler = LogHandler(logPath, refreshPeriod, treshold, monitorDuration)
logHandler.start()
