# Run a the HTTP monitor along with an entry generator on a simulated log file

from entry_generator import EntryGenerator
from log_handler import LogHandler
from time import sleep
import configparser
import os


config = configparser.ConfigParser()
config.read("parameters.cfg")

logPath = str(config.get("Simulation", "logPath"))
if os.path.isfile(logPath):
    os.remove(logPath)
refreshPeriod = float(config.get("Simulation", "refreshPeriod"))
treshold = float(config.get("Simulation", "treshold"))
monitorDuration = float(config.get("Simulation", "monitorDuration"))
generationRate = float(config.get("Simulation", "generationRate"))
entryGenerator = EntryGenerator(logPath, generationRate)
logHandler = LogHandler(logPath, refreshPeriod, treshold, monitorDuration)
entryGenerator.start()
sleep(1)
logHandler.start()
