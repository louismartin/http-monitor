# Run a the HTTP monitor along with an entry generator on a simulated log file

from classes.entry_generator import EntryGenerator
from classes.log_handler import LogHandler
from time import sleep
import configparser


config = configparser.ConfigParser()
config.read("parameters.cfg")

logPath = str(config.get("Simulation", "logPath"))
refreshPeriod = int(config.get("Simulation", "refreshPeriod"))
treshold = int(config.get("Simulation", "treshold"))
monitorDuration = int(config.get("Simulation", "monitorDuration"))
generationRate = int(config.get("Simulation", "generationRate"))
entryGenerator = EntryGenerator(logPath, generationRate)
logHandler = LogHandler(logPath, refreshPeriod, treshold, monitorDuration)
entryGenerator.start()
sleep(1)
logHandler.start()
