# -*-coding:Latin-1 -*

from classes.log_handler import *
from classes.log_entry import *
import configparser





config = configparser.ConfigParser()
config.read("parameters.cfg")

logPath = str(config.get("Monitor","logPath"))
refreshPeriod = int(config.get("Monitor","refreshPeriod"))
treshold = int(config.get("Monitor","treshold"))
monitorDuration = int(config.get("Monitor","monitorDuration"))
logHandler = LogHandler(logPath, refreshPeriod, treshold, monitorDuration)
logHandler.start()
