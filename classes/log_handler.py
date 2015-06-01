# The LogHandler object is a thread that handles the processing and monitoring of the log

from classes.log_entry import *
from collections import deque,Counter
from time import sleep
from datetime import datetime
from datetime import timedelta
from threading import Thread
from sys import stdout
import os

 

class LogHandler(Thread):
    """Handles the processing and monitoring of the log"""
    
    def __init__(self, logPath, refreshPeriod, alertThreshold, monitorDuration):
        """Constructor

        :param logPath: path of the log file
        :param refreshPeriod: Period to check on the log in seconds
        :param alertThreshold: Number of hits to trigger alarm
        :param monitorDuration: Data is only kept during this time in seconds
        """
        
        Thread.__init__(self)
        self.logPath = logPath
        self.refreshPeriod = refreshPeriod
        self.alertThreshold = alertThreshold
        self.monitorDuration = monitorDuration
        # initialize lastReadTime: current time - monitorDuration (to only process this time frame)
        self.lastReadTime = datetime.now() - timedelta(seconds = self.monitorDuration)
        # Attribute where we will store the log entries (list-like container with fast appends and pops on either end)
        self.log = deque()
        # Set it to False to stop the monitoring loop (call stop())
        self.running = True
        self.hits = 0
        self.size = 0
        # Counter: dict subclass for counting hashable objects
        self.sections = Counter() 
        self.ips = Counter()
        self.methods = Counter()
        self.codes = Counter()
        self.alertStatus = False
        # Set it to False to stop displaying messages in the console
        self.printStatus = True
        # Alerts messages will be stored in this string
        self.alerts = ""

    def add_entry(self,entry):
        """Adds an LogEntry to the handler and updates stats"""
        if entry.parsed:
            self.log.append(entry)
            self.hits += 1
            self.size += entry.size
            self.sections[entry.section] += 1
            self.ips[entry.ip] += 1
            self.methods[entry.method] += 1
            self.codes[entry.code] += 1

    def delete_entry(self):
        """Deletes oldest entry of the handler and updates stats"""
        entry = self.log.popleft()
        self.hits -= 1
        self.size -= entry.size

        # When a Counter key has a value of 0 I prefer removing it
        self.sections[entry.section] -= 1
        if self.sections[entry.section] == 0:
            del self.sections[entry.section]
            
        self.ips[entry.ip] -= 1
        if self.ips[entry.ip] == 0:
            del self.ips[entry.ip]
            
        self.methods[entry.method] -= 1
        if self.methods[entry.method] == 0:
            del self.methods[entry.method]
            
        self.codes[entry.code] -= 1
        if self.codes[entry.code] == 0:
            del self.codes[entry.code]

    def read(self):
        """Reads the log file and adds entries that happened during the monitored time frame"""
        # Store lastReadTime value temporarily (attribute updated next line)
        lastReadTime = self.lastReadTime
        # Update the lastReadTime before reading file so as not to miss any value next time
        now = datetime.now()
        # Remove microseconds
        self.lastReadTime = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second) 
        try:
            with open(self.logPath,"r") as logFile:
                lines = logFile.readlines()

            # iterate over lines in reversed order (most recent first) of entries in the monitored time frame
            i=1
            while i <= len(lines) and LogEntry(lines[-i]).time>=lastReadTime:
                logEntry = LogEntry(lines[-i])
                if logEntry.time>lastReadTime:
                    self.add_entry(logEntry)

                # entries dated at the same second might already have been added
                elif logEntry.time == lastReadTime:    
                    if logEntry not in self.log:
                        self.add_entry(logEntry)
                i+=1
        except:
            print("*** ERROR: LogHandler cannot read the log file ***\n\n")
            self.running = False
            input("PRESS ENTER TO EXIT")

    def drop_old_entries(self):
        """Remove entries older than the monitored duration"""
        # while first element (assumiing it's the oldest) of log is too old, remove it
        while len(self.log) != 0 and self.log[0].time<(self.lastReadTime - timedelta(seconds = self.monitorDuration)):    
            self.delete_entry()

            
    def alert(self):
        """Triggers an alert when hits are too high"""
        alert = ("[%s] High traffic generated an alert - hits = %d\n"
                % (datetime.now().strftime("%d/%b/%Y:%H:%M:%S"),self.hits))
        # Add the alert message before all the other messages
        self.alerts = alert + self.alerts
        # Store this alert in a file to keep history
        try:
            with open("alerts.log","a") as alertLog:
                alertLog.write(alert)
        except:
            print("Cannot write alerts to alerts.log")
        self.alertStatus = True

    def end_alert(self):
        """Ends the alert when traffic recovered"""
        alert = ("[%s] Traffic slowed down, the alert has recovered\n"
                % (datetime.now().strftime("%d/%b/%Y:%H:%M:%S")))
        self.alerts = alert + self.alerts
        with open("alerts.log","a") as alertLog:
            alertLog.write(alert)
        self.alertStatus = False

    def stop(self):
        """Stops the monitoring loop"""
        self.running = False

    def display_message(self):
        """Creates and displays all informations in the console"""
        consoleMessage = "**************************\nWelcome to HTTP Monitor!\n**************************\n\n"
        consoleMessage += "Parameters:\n"
        consoleMessage += "Alert threshold = %d hits     Refresh period = %ds     Monitor duration = %ds\n\n\n" % (self.alertThreshold, self.refreshPeriod, self.monitorDuration)

        consoleMessage += "Summary:\n"
        consoleMessage += "Current hits: %d" % self.hits
        if self.alertStatus:
            consoleMessage += " > %d         **********ALERT**********\n" % self.alertThreshold
        else:
            consoleMessage += "                    Everything OK\n"
        consoleMessage += "\nClient data: %d Kb" % (self.size/1000)
        consoleMessage += "\nSections     -> " + self.summary(self.sections)
        consoleMessage += "\nClients      -> " + self.summary(self.ips)
        consoleMessage += "\nStatus codes -> " + self.summary(self.codes)
        consoleMessage += "\nMethods      -> " + self.summary(self.methods)
        consoleMessage += "\n\n\n"
        consoleMessage += "Alerts (Stored in real time in alerts.log):\n"
        consoleMessage += self.alerts
        # Clear the console of previous message so that it appears to be refreshed
        os.system("cls")
        print(consoleMessage, end="\r") 

    def summary(self,items):
        """Returns a String summary of a particular Counter object
        :param items: Counter object to be summarized"""
        summary = ""
        for item in items.most_common(3):
            summary += str(item[0])+" (%d%%)   " % (item[1]/self.hits*100)
        return summary
       
        
    def run(self):
        """Method called when thread is started, main monitoring loop"""
        # Loop stops when stop() is called
        while self.running:
            self.read()
            # If log file cannot be accessed self.running is set to false
            if self.running:
                self.drop_old_entries()
                # if threshold is exceeded but the alert was not activated before, call alert()
                if self.hits > self.alertThreshold and not self.alertStatus:
                    self.alert()
                # else, if the alert is on but hits went below the threshold, end the alert
                elif self.hits < self.alertThreshold and self.alertStatus:
                    self.end_alert()
                # Check if the console output is enabled
                if self.printStatus:
                    self.display_message()
                sleep(self.refreshPeriod)    
        
