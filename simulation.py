# -*-coding:Latin-1 -*

from classes.entry_generator import *
from classes.log_handler import *
from classes.log_entry import *
import configparser


config = configparser.ConfigParser()
config.read("parameters.cfg")

logPath = str(config.get("Simulation","logPath"))
refreshPeriod = int(config.get("Simulation","refreshPeriod"))
treshold = int(config.get("Simulation","treshold"))
monitorDuration = int(config.get("Simulation","monitorDuration"))
generationRate = int(config.get("Simulation","generationRate"))
entryGenerator = EntryGenerator(logPath, generationRate)
logHandler = LogHandler(logPath, refreshPeriod, treshold, monitorDuration)
entryGenerator.start()
sleep(1)
logHandler.start()
