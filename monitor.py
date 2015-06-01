# Run the HTTP monitor with parameters from parameters.cfg

from classes.log_handler import LogHandler
import configparser


config = configparser.ConfigParser()
config.read("parameters.cfg")

logPath = str(config.get("Monitor", "logPath"))
refreshPeriod = int(config.get("Monitor", "refreshPeriod"))
treshold = int(config.get("Monitor", "treshold"))
monitorDuration = int(config.get("Monitor", "monitorDuration"))
logHandler = LogHandler(logPath, refreshPeriod, treshold, monitorDuration)
logHandler.start()
